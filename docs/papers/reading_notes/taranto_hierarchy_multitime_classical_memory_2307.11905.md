# Reading note (精读): Taranto, Quintino, Murao, Milz, "Characterising the Hierarchy of Multi-time Quantum Processes with Classical Memory" (arXiv:2307.11905)

> **Provenance (2026-07-06): FULL-TEXT read (精读) via ar5iv HTML
> (https://ar5iv.labs.arxiv.org/abs/2307.11905).** Definitions/Eqs transcribed from that
> rendering. Published as Quantum 8, 1328 (2024).
> **NOTE (2026-07-06 rewrite):** this note REPLACES an earlier 2026-07-05 version that
> misnamed the hierarchy ("Mixed Memory") and — critically — wrongly claimed the CM class
> is a PASSIVE-record HMM null. The corrected reading below is load-bearing for Flag #1
> (is quantum memory expressed on the PASSIVE syndrome record, or only in an ACTIVE,
> instrument-varying object?). Taranto's classical memory is defined via ACTIVE
> feed-forward instruments, NOT a passive outcome record.
>
> Adjudication target (Flag 0 / notion-2): (1) the exact definition of a multi-time
> process with CLASSICAL memory = our notion-2 matched null; (2) the hierarchy levels
> and the Markov < classical < quantum separations proving non-Markovian ≠ quantum;
> (3) whether classical memory is defined on a passive RECORD or via interventions.

## Metadata [paper]

- **Authors:** Philip Taranto, Marco Túlio Quintino, Mio Murao, Simon Milz
- **Venue / status:** arXiv:2307.11905 [quant-ph] → Quantum 8, 1328 (2024)
- **Type:** theory — process-tensor / higher-order-map framework; strict-inclusion
  classification of multi-time memory classes with explicit separating examples.

## Executive summary [paper]

Multi-time quantum processes are represented as process tensors (higher-order maps,
composed via the link product ⋆). The paper defines a **strict hierarchy of memory
classes** distinguished by HOW the environment carries information between the times at
which an experimenter intervenes. Between successive intervention times the environment
undergoes a channel; the class is fixed by what that channel is allowed to be:

- **Quantum Memory (QM)** — Def. 1: general process; environment channel is an arbitrary
  identity/coherent channel (Eq. 6). The environment carries genuinely quantum
  correlations across time.
- **Separable (SEP)** — Def. 5: process tensor separable across the time cuts.
- **Classical Memory (CM)** — Def. 3: the environment is hit by an **entanglement-breaking
  channel (EBC)** between each pair of times (Eq. 12/13). Information across time is
  carried by a classical variable, but that variable can be **fed forward to condition
  future dynamics** (active feed-forward).
- **Classical Direct Cause (CDC)** — Def. 4: a single classical common-cause variable x
  is drawn once (with prob p_x) and used to pick the whole trajectory of channels
  (Eq. of Def. 4). No round-by-round feed-forward.
- **Memoryless (M)** — Def. 2: trace-and-prepare channel between times (Eq. 9); the
  process factorizes, no temporal correlation.

**Main theorem (Theorem 1):** for **N ≥ 3** times the inclusions are all STRICT:

```
𝙼  ⊊  𝙲𝙳𝙲  ⊊  𝙲𝙼  ⊊  𝚂𝙴𝙿  ⊊  𝚀𝙼
```

For **N = 2** times CM and CDC coincide and several distinctions collapse — the genuine
separations only appear at three-or-more times. This is the exact "you need ≥3 times to
tell classical from quantum memory" statement.

**Non-Markovian ≠ quantum:** every class above M is non-Markovian (has temporal memory),
yet M ⊊ CDC ⊊ CM all sit BELOW the quantum-memory boundary SEP/QM. So a process can be
strongly non-Markovian (CM/CDC) with purely classical memory. This is the formal backbone
for our in-house result that a negativity/backflow revival witnesses non-Markovianity but
NOT quantumness.

## Key equations / criteria [paper]

Composition is the **link product** ⋆ (Eq. 5). Superscripts i/o denote the input/output
legs of the system (s) and environment (e) at each time; subscripts index the time.

### Quantum Memory (general process) — Def. 1, Eq. (6)
General process tensor; between times the environment evolves under an arbitrary
(identity/coherent) channel. This is the top of the hierarchy 𝚀𝙼.

### Memoryless — Def. 2, Eq. (9)
The inter-time environment channel is a **trace-and-prepare** channel (discard the
environment, prepare a fixed state) ⇒ the process factorizes across times.

### Classical Memory (CM) — Def. 3, Eq. (12) [VERBATIM]
> "An N-time classical memory quantum process is represented by a process
> 𝖢ᴺ:₁ᶜᴹ ≥ 0 that can be written as
> 𝖢ᴺ:₁ᶜᴹ = 𝟙ₑₙᵢ ⋆ (⋆ⱼ₌₁ᴺ⁻¹ 𝖴₍ₑₛ₎ⱼ₊₁ⁱʲᵒ ⋆ 𝖤ₑⱼ) ⋆ ρ₍ₑₛ₎₁ⁱ"

where each **𝖤ₑⱼ is an entanglement-breaking channel (EBC) on the environment** at time j.

**EBC = measure-and-prepare (Eq. defining EBC, p.12) [VERBATIM]:**
> "EBCs are described by measure-and-prepare channels, i.e.,
> 𝖤ₒᵢ = ∑ₓ σₒ⁽ˣ⁾ ⊗ 𝖬ᵢ⁽ˣ⁾ where each σₒ⁽ˣ⁾ is an arbitrary state and {𝖬ᵢ⁽ˣ⁾} forms a POVM."

**Equivalent conditional form — Eq. (13):**
```
𝖢ᴺ:₁ᶜᴹ = Σ_{xₙ:₁} 𝖫ᴺⁱ:ᴺ⁻¹ᵒ⁽ˣᴺ|ˣᴺ⁻¹:₁⁾ ⊗ … ⊗ 𝖫₂ⁱ:₁ᵒ⁽ˣ²|ˣ₁⁾ ⊗ ρ₁ⁱ⁽ˣ¹⁾
```
Each 𝖫 is a CPTP channel labelled by classical outcomes; the outcome x_j is **fed forward**
to condition every future channel. Paper text (p.12–13) [VERBATIM]:
> "The classical label corresponding to any observed outcome x₁ can be stored and fed
> forward to condition the overall choice of any future EBC."

### Classical Direct Cause (CDC) — Def. 4, Eq. of Def. 4 [VERBATIM]
> "An N-time classical direct cause quantum process is represented by a process
> 𝖢ᴺ:₁ᶜᵈᶜ ≥ 0 that can be written as
> 𝖢ᴺ:₁ᶜᵈᶜ = ∑ₓ pₓ 𝖫ᴺⁱ:ᴺ⁻¹ᵒ⁽ˣ⁾ ⊗ … ⊗ 𝖫₂ⁱ:₁ᵒ⁽ˣ⁾ ⊗ ρ₁ⁱ⁽ˣ⁾"

where p_x is a probability distribution and each 𝖫ⱼ₊₁ⁱ:ⱼᵒ⁽ˣ⁾ is CPTP. Difference from CM:
ONE global classical variable x for the whole run (common cause), NOT round-by-round
re-measured/fed-forward outcomes.

### Hierarchy — Theorem 1 [VERBATIM inclusion, N ≥ 3]
```
𝙼 ⊊ 𝙲𝙳𝙲 ⊊ 𝙲𝙼 ⊊ 𝚂𝙴𝙿 ⊊ 𝚀𝙼
```
- Class map: 𝙼 = Memoryless (Def. 2), 𝙲𝙳𝙲 = Classical Direct Cause (Def. 4),
  𝙲𝙼 = Classical Memory (Def. 3), 𝚂𝙴𝙿 = Separable (Def. 5), 𝚀𝙼 = general process (Def. 1).
- Two-time collapse [VERBATIM, App. B / p.18–19]: "For two-time processes, 𝙲𝙼 and 𝙲𝙳𝙲
  coincide"; "on more than two times, the sets differ." Strict inclusions hold only for
  N ≥ 3.

## Relevance to project [ours]

**Flag 0 (notion-2 matched null) — what "classical memory" actually is, and the
CORRECT null.**

1. **CM is our notion-2 null, but it is an ACTIVE/instrument object, not a passive
   record.** [paper] Def. 3 defines CM through EBCs = **measure-and-prepare channels that
   feed classical outcomes FORWARD to condition future channels** (Eq. 12/13). This is an
   interventional construction: the "measurement" is a live POVM inserted BETWEEN the
   experimenter's operations, whose outcome is used to steer subsequent dynamics.
   [ours] Therefore Taranto's CM/QM boundary is a statement about the process tensor as a
   higher-order map probed by VARYING instruments — NOT a statement about the marginal
   statistics of a single fixed passive measurement sequence. This is direct evidence for
   **Flag #1**: the quantum-memory content sits in the active, instrument-varying object,
   and is not, on its face, guaranteed to be expressed on our PASSIVE syndrome record.

2. **Non-Markovian ≠ quantum is a theorem here, not a heuristic.** [paper] M ⊊ CDC ⊊ CM
   are all non-Markovian yet all strictly below SEP/QM. [ours] This is exactly the formal
   home of our Control-0b result: a classical (RTN-dephasing) process is at most CM, has
   genuine temporal memory (fires a bare non-Markovianity / negativity-revival witness),
   and yet carries NO quantum memory. A bare revival witness lives at the M-vs-{CDC,CM,…}
   boundary (memory vs no-memory), NOT at the CM-vs-QM boundary (classical vs quantum).
   Bäcker's E♯[χ₁] < E[χ₂] (2310.01205 Thm 1) is the CM-vs-QM boundary witness; the "#"
   (assistance) is precisely the "beats the best classical-memory model" content that a
   bare revival drops.

3. **≥3 times is mandatory for the classical-vs-quantum question.** [paper] For N = 2, CM
   = CDC and the separations collapse; strictness needs N ≥ 3. [ours] Any attempt to
   separate classical from quantum memory from TWO-time correlations (e.g. 2-point
   matched-marginal TV) is structurally incapable of it — consistent with the standing
   memory note that the right observable is multi-time (p_ij / process-tensor), never a
   2-point statistic. But note the caveat in point 1: Taranto's multi-time object is the
   instrument-varying process tensor, not the passive multi-time record; whether a passive
   N≥3 syndrome record inherits the separation is the open Flag-#1 question, NOT settled by
   this paper.

4. **CDC vs CM as two flavours of classical null.** [ours] Our shared-latent source (a
   single latent bath variable imprinting all rounds) is closer to **CDC** (one common-cause
   x drawn once) than to full CM (round-by-round re-measured feed-forward). Both are
   classical (below SEP/QM), so either is a valid classical-memory matched null; but the
   distinction matters if we ever fit the null generatively — CDC is a mixture-of-product
   channels, CM is a conditional/HMM-like chain.

## Decisive verbatim quotes [paper]

- CM definition (Def. 3, Eq. 12): "An N-time classical memory quantum process is
  represented by a process 𝖢ᴺ:₁ᶜᴹ ≥ 0 that can be written as
  𝖢ᴺ:₁ᶜᴹ = 𝟙ₑₙᵢ ⋆ (⋆ⱼ₌₁ᴺ⁻¹ 𝖴₍ₑₛ₎ⱼ₊₁ⁱʲᵒ ⋆ 𝖤ₑⱼ) ⋆ ρ₍ₑₛ₎₁ⁱ" — with each 𝖤ₑⱼ "an
  entanglement-breaking channel (EBC) on the environment at each time."
- EBC form: "EBCs are described by measure-and-prepare channels, i.e.,
  𝖤ₒᵢ = ∑ₓ σₒ⁽ˣ⁾ ⊗ 𝖬ᵢ⁽ˣ⁾ where each σₒ⁽ˣ⁾ is an arbitrary state and {𝖬ᵢ⁽ˣ⁾} forms a POVM."
- Feed-forward (active) character: "The classical label corresponding to any observed
  outcome x₁ can be stored and fed forward to condition the overall choice of any future
  EBC." / "in each run, any EBC can simply measure the system and feed forward classical
  information pertaining to the outcome."
- Hierarchy (Thm 1): "𝙼 ⊊ 𝙲𝙳𝙲 ⊊ 𝙲𝙼 ⊊ 𝚂𝙴𝙿 ⊊ 𝚀𝙼" for N ≥ 3.
- Two-time collapse: "For two-time processes, 𝙲𝙼 and 𝙲𝙳𝙲 coincide"; "on more than two
  times, the sets differ."

## Limitations / provenance caveats

- [ours] The strongest Flag-#1 statement — "quantum memory is detectable ONLY by varying
  instruments, a single fixed passive measurement yields classically-reproducible
  statistics" — is an INFERENCE consistent with the framework (memory classes are
  properties of the process tensor probed by varying instruments) but was NOT lifted from
  a single verbatim theorem sentence in this fetch. Treat it as [ours] provisional, to be
  confirmed against the non-signalling / instrument-dependence discussion (paper §2.1 and
  the NS-process discussion) before it is load-bearing.
- Definitions transcribed from ar5iv HTML; unicode sub/superscripts on the link-product
  expressions may not be byte-perfect. The STRUCTURE (EBC feed-forward, hierarchy order,
  N≥3 strictness, 2-time collapse) is confirmed across multiple fetches.

## Tags

- `[paper]` strict hierarchy (N≥3): 𝙼 ⊊ 𝙲𝙳𝙲 ⊊ 𝙲𝙼 ⊊ 𝚂𝙴𝙿 ⊊ 𝚀𝙼
- `[paper]` CM = entanglement-breaking (measure-and-prepare) channel between times, with
  classical outcome FED FORWARD (active) — Def. 3, Eq. 12/13
- `[paper]` CDC = single global common-cause classical variable — Def. 4
- `[paper]` two-time: CM = CDC (hierarchy collapses); strict only for N ≥ 3
- `[ours]` CM/CDC are the notion-2 classical-memory matched null; both non-Markovian, both
  below the SEP/QM quantum-memory boundary ⇒ non-Markovian ≠ quantum (formal home of
  Control-0b)
- `[ours]` CM is defined on an ACTIVE feed-forward/instrument object, NOT a passive record
  ⇒ direct evidence for Flag #1 (passive syndrome record may not inherit the separation)
- `[ours]` bare revival witnesses M-vs-memory boundary, NOT CM-vs-QM; Bäcker's E♯<E is the
  CM/QM witness (the "#" = beats best classical-memory model)
