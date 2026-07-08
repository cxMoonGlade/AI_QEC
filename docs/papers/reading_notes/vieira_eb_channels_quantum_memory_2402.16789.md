# Reading note (精读): Vieira, Ku, Budroni, "Entanglement-Breaking Channels Are a Quantum Memory Resource" (arXiv:2402.16789)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** HTML → txt `outputs/papers/2402.16789.txt`
> (7 pages, Phys. Rev. Research 7, 043281, 2025). All §/Eq refs from that text.
> Adjudication target: does the entanglement-breaking condition, which determines
> the "Classical Memory" rung in the Taranto hierarchy, actually guarantee
> classical simulability of the multi-time statistics? **Verdict: NO — EB channels
> are NOT classically simulable in multi-time scenarios; the Taranto hierarchy's
> classical-memory rung is weaker than true classicality.**

## Metadata [paper]

- **Authors:** Gabriel H. Vieira, Huan-Yu Ku, Costantino Budroni (Universitat de
  les Illes Balears / Academia Sinica / University of Vienna)
- **Venue / status:** arXiv:2402.16789v2 [quant-ph], 3 Oct 2024 → Phys. Rev.
  Research 7, 043281 (2025)
- **Type:** theory (counterexample + hierarchy refinement)

## Executive summary [paper]

The Taranto et al. hierarchy classifies multi-time quantum processes by the
quantum resources required for their simulation. The "Classical Memory" (CM)
rung is defined by entanglement-breaking (EB) channels between time steps —
the environment is replaced by a classical system at each step. **This paper
shows the CM rung does NOT correspond to classically simulable dynamics.**

**Core finding:** A qudit passing through an entanglement-breaking channel can
generate genuinely nonclassical temporal correlations that cannot be simulated
by a classical system (dit) of the same dimension. The paper provides an
explicit counterexample: a memory-based output generation task where EB-channel
dynamics outperform optimal classical strategies.

**Practical implication:** The entanglement-breaking condition between rounds is
not sufficient to guarantee the process is classically simulable. The "classical
memory" label in the Taranto hierarchy is a misnomer — these processes may
require genuine quantum resources, just not entanglement across the system-
environment cut at a single time.

**Why this matters for the user:** The user's shared-mode σ− relaxation may
appear to be in the CM rung (the bosonic mode acts as an environment that can
be entanglement-broken between syndrome rounds at high γ). But this paper shows
that EB status does NOT certify classical simulability — the multi-time
statistics may still be nonclassical, even when single-round channel is EB.

### Hierarchy clarification

The Taranto hierarchy organizes multi-time processes into rungs by the quantum
memory required:

1. **Markovian** (no memory — product channels)
2. **Classical Memory** (memory carried by a classical system; EB channels)
3. **Quantum Memory** (memory carried by a quantum system)

Vieira et al. show that rung 2 (CM via EB) does not collapse to classical
statistics. The hierarchy should be refined: the EB condition is not the
classicality delimiter. A stricter condition (e.g., simulability by a hidden
Markov model with finite classical memory) is required for genuine classicality.

### Explicit counterexample

The paper constructs a memory-based output generation task where:

- Input: a binary string x₁, ..., xₙ
- Output: a binary prediction yₜ at each time step
- An EB-channel-based strategy achieves success probability p_success > classical
  bound
- The advantage arises from genuinely quantum temporal correlations that survive
  the EB channel

## Key equations/findings [paper]

### Entanglement-breaking channel definition

A channel ℰ is entanglement-breaking iff its Choi state is separable:

```
χ_ℰ = (ℰ⊗𝟙)|ϕ⁺⟩⟨ϕ⁺|  is  separable  ⇔  ℰ is EB
```

Equivalently, ℰ admits the Holevo form:

```
ℰ[ρ] = Σ_k |ψ_k⟩⟨ψ_k|  tr[ρ M_k]
```

where |ψ_k⟩ are pure states and {M_k} is a POVM. The output is always a
separable state — no entanglement survives the channel.

### EB is not classical

The key inequality that separates EB dynamics from true classical simulation:

For a classical hidden Markov model with d-dimensional memory:

```
p_success_classical ≤ f(d, n)
```

whereas the EB-channel model achieves:

```
p_success_EB > f(d, n)  for some n
```

The advantage persists even for arbitrarily long sequences — it is not a
finite-size effect.

### Relation to non-Markovianity

- EB channels are non-Markovian in the sense of having memory between steps
  (the process is not a product of independent channels).
- But they were previously considered the "mildest" form of non-Markovianity —
  this paper shows they can generate correlations beyond any classical model.
- **Surprising corollary:** even processes that are "merely" non-Markovian via
  EB channels (no entanglement across the s-e cut at any single time) can
  require quantum resources for their multi-time simulation.

## Relevance to project [ours]

**Claim 3 — "is the finite-γ memory in shared-mode σ− relaxation classically
expressible?"** This paper provides a CRITICAL CAVEAT to the Claim 3 analysis.
Here is why:

1. **Taranto hierarchy maps to the user's model:** In the user's setup, the
   bosonic mode acts as the memory between syndrome rounds. The relevant
   question is where this memory sits in the Taranto hierarchy. At high γ,
   the effective channel between mode and qubits may be entanglement-broken
   between rounds, suggesting placement in the "Classical Memory" rung.

2. **BUT: the CM rung does NOT mean classical simulable:** Vieira et al.
   demonstrate that an entanglement-breaking channel between rounds is a
   necessary but NOT sufficient condition for classical simulability of the
   multi-time process. The user CANNOT conclude "classical enough" from the
   single-round EB status alone.

3. **Implication for γ=0.15:** Even if the shared mode is entanglement-broken
   between syndrome rounds at γ=0.15 (which it may well be — the mode decay
   rapidly destroys entanglement with the data qubits), the multi-time
   statistics may still be nonclassical. The memory defies classical
   simulation even though no round-to-round entanglement survives.

4. **The real threshold is stricter:** The user's conjecture that the finite-γ
   memory is "classically expressible" needs a stronger witness than EB status.
   The Bäcker criteria (entanglement of assistance, entropic witness) are the
   appropriate tools — they probe the multi-time correlations, not the single-
   round structure.

5. **Process-tensor witness:** The true test of classical simulability requires
   analyzing the full process tensor (multi-time correlations), not just the
   single-round channels. This paper implies the user should NOT shortcut the
   analysis via single-round EB checks.

6. **Practical guidance for the user's analysis:**
   - Do NOT use EB as a classicality certificate
   - DO apply the Bäcker E♯ criterion (backer_local_disclosure...) for
     two-time witnesses
   - DO apply the entropic witness (backer_entropic_witness...) for
     scalable multi-time checks
   - If both witnesses fail to fire AND the EB condition holds, this is
     suggestive but NOT conclusive — a full process-tensor analysis or
     explicit classical simulation attempt is needed for the definitive
     verdict

### Concrete steps for the user

1. Compute the single-round channel ℰ (qubits after interaction with mode) at
   γ=0.15. Is it EB? (Compute Choi state, check separability.)
2. Even if EB: apply the Bäcker E♯ witness to the two-time channels
   (ℰ₁, ℰ₂) from the JC reduced dynamics.
3. If E♯ fires: quantum memory confirmed, Claim 3 refuted.
4. If E♯ does NOT fire: inconclusive — the memory may still be nonclassical
   (this paper shows EB channels can produce nonclassical multi-time
   correlations that evade two-time witnesses).
5. For the definitive test: construct a classical hidden Markov model with
   d=dim(mode) memory and compare its multi-time statistics to the JC model.
   If the classical model reproduces all multi-time correlations exactly,
   Claim 3 is confirmed.

## Limitations

- **Single-qudit counterexamples:** the explicit nonclassical EB examples
  are for single qudits. Extension to the user's 2-qubit + bosonic mode
  setup is conceptually straightforward but numerically non-trivial.
- **No constructive classical simulation failure bound:** the paper shows
  EB does NOT imply classical simulability, but does not provide an
  algorithm for deciding classical simulability of a given EB process.
- **Small advantage regime:** the nonclassical advantage over classical
  memory may be small for some parameter ranges — quantifying it at
  γ=0.15 requires explicit computation.
- **Process tensor formalism needed:** the paper's analysis is in the
  process tensor framework. Translating to the user's JC model requires
  constructing the process tensor for the joint qubit-mode dynamics.

## Tags

- `[paper]` EB channels are NOT classically simulable in multi-time settings
- `[paper]` Taranto hierarchy CM rung does NOT imply classical statistics
- `[paper]` explicit counterexample: EB-channel strategy > optimal classical strategy
- `[paper]` non-Markovianity via EB can require quantum resources
- `[ours]` CRITICAL CAVEAT: do NOT use EB status to certify classicality
- `[ours]` γ=0.15 may be EB between rounds but still nonclassical in multi-time
- `[ours]` strengthens case for applying Bäcker witnesses (E♯, entropic) over EB checks
- `[ours]` ultimate test: explicit classical HMM vs JC model comparison
