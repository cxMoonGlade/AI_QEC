# Quantum-back-action DEEPEN — derivation + predictions (predict-before-measure, 2026-07-04)

> **HISTORICAL INTERPRETATION SUPERSEDED, 2026-07-13.** Preserve the run facts, but `K` is a
> measure-all/omit non-invasiveness comparison, not a coherence or quantum-memory certificate, and
> the three-time `M_mem` statistic is a local conditional-dependence diagnostic rather than an `iff`
> test of the full record's Markov order. Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

**Status: DERIVATION written BEFORE the run.** Committed script:
`outputs/twin_validation/quantum_backaction_deepen.py`. Deepens the C4-analog per the user's correction
(2026-07-04): **K certifies COHERENCE / non-classicality, NOT a non-Markovian bath** — a coherent Markovian
*control* (QC2, no bath) forges K>0. So the "quantum non-Markovian bath" headline needs the CONJUNCTION of
coherence (K) AND memory (multi-time), plus the two standing red-team kill-shots (joint-parity twirl,
effect-size). This is "revived pending deepen", not proven.

Anchors: milz 1907.05807 (Kolmogorov = classicality; measurement-class dependence); the C4-analog v2 (K, two
bases); the notion-2 best-Markov-k memory machinery; noise_adapted 2411.09637.

## The two statistics

- **K (protocol non-invasiveness), both bases:** `K = Σ_{s1,s3}|Σ_{s2}P_all(s1,s2,s3) − P_skip2(s1,s3)|`
  (Milz Eq. 9). `K>0` witnesses inconsistency/invasiveness for this protocol family; it does not
  identify coherence, the bath, or the memory carrier. A Markovian coherent control can make it positive.
- **M_mem (memory / non-Markovian, the NEW discriminator):** the record's departure from Markov-order-1 —
  `M_mem = Σ_{s1,s2,s3}|P_all(s1,s2,s3) − P(s1,s2)·P(s2,s3)/P(s2)|` (tests `s1 ⊥ s3 | s2`).
  Markov-1 implies `M_mem=0`; the reverse proves only this local three-time conditional independence.
  `M_mem>0` refutes Markov-1 for the tested marginal, while `M_mem=0` does not certify the full process.

**The 2-D classification (K × M_mem) is the headline:**

| object | K (coherence) | M_mem (memory) | reading |
|---|---|---|---|
| classical memoryful noise (correlated incoherent, our 1/f) | **0** | **>0** | **notion-2** (memory, no coherence) |
| coherent Markovian CONTROL (σx drive / gate over-rotation, no bath) | **>0** | **0** | coherent but memoryless — NOT a bath |
| **quantum non-Markovian BATH** (coherent coupling + persistent bath) | **>0** | **>0** | **the headline — coherence AND memory** |

## PREDICTIONS (predict-before-measure)

- **DM1 (the 2-D classification, a-exact):** the three rows above are realized exactly —
  - classical memoryful (2-state correlated latent, incoherent Pauli-Z emission): K(Z)=K(X)=0, M_mem>0.
  - coherent Markovian control (`H=(Ω/2)σ_x`, identical each round, no bath, measure σz): K(Z)>0, **M_mem=0**
    (the post-measurement collapse makes the outcome record Markov-1). ⇒ **K alone does NOT certify a bath.**
  - quantum non-Markovian bath (`H=g σ_z^S σ_z^B`, persistent bath, measure X): K(X)>0 AND **M_mem>0** (the
    bath correlates rounds beyond Markov-1). ⇒ the CONJUNCTION is the quantum-non-Markovian-bath signature.
- **DM2 (joint-parity twirl, the standing kill-shot):** replace the rank-1 direct σx read with a rank-2
  DEGENERATE joint-parity `X_S X_{S2}` (a 2-qubit stabilizer proxy, ancilla-mediated real-measurement class,
  Milz measurement-class restriction). Predict (UNCERTAIN — this is why we check): K survives but REDUCED
  (the parity still detects the σz error noncommuting) — **OR** K→0 (the degeneracy twirls the coherence). If
  K→0 under joint-parity, the rank-1 survival was an artifact ⇒ the real stabilizer twirls it ⇒ notion-2
  ceiling. FALSIFIER either way — reported honestly.
- **DM3 (effect-size, a-exact scaling):** at physical coherent coupling angle `θ` (per-round coherent error
  ~1e-2 rad, vs the toy's π/3), K and M_mem `∝ θ²` (leading order) ⇒ feasible-N to detect at 3σ `∝ θ^{−4}`.
  Report the K(θ), M_mem(θ) curve + the feasible-N at a physical θ. If feasible-N ≫ 1e6 at physical θ, the
  headline is sub-feasible even if it survives DM1/DM2 (a real cap).

## Verdict rule (predict-before-measure)

- **Quantum-dephasing headline STANDS** iff: DM1 shows the bath has K>0 ∧ M_mem>0 while the coherent control
  has M_mem=0 (memory separates them); DM2 K survives the joint-parity twirl; DM3 feasible-N at physical θ is
  ≤ 1e6. Then it is passive-record-legitimate (two bases + memory + real-measurement + feasible), shares the
  notion-2 plumbing (dense carrier + per-round SPAM), source-swap only.
- **FALL BACK to notion-2 ceiling** iff DM1 fails (coherent control also has M_mem>0 — memory can't separate),
  or DM2 fails (joint-parity twirls K→0), or DM3 fails (feasible-N ≫ 1e6). Each is a real, reportable finding.

## RESULTS (post-run 2026-07-04; predictions above INTACT)

Committed: `outputs/twin_validation/quantum_backaction_deepen.py` (`python-exit=0`,
`content_hash=d6c2df7fef5c45d58fb5d20dee5283ad032a43876f98f25ec14b4ee3fd2b11f7`,
`GATE_RESULT ... FALLBACK_NOTION2`).

| # | prediction | result | verdict |
|---|---|---|---|
| DM1 classical | K=0/0, M_mem>0 | K=0, **M_mem=0.102** | **CONFIRMED — notion-2** |
| DM1 coherent control | K>0, M_mem=0 | K(Z)=0.75, **M_mem=0** | **CONFIRMED — coherent, memoryless** |
| DM1 quantum bath | K>0 **∧** M_mem>0 (headline) | K(X)=0.75, **M_mem≈0** | **MISS — toy bath has NO record memory** |
| DM2 joint-parity twirl | K survives (uncertain) | rank-2 parity K=0.75 = rank-1 | **CONFIRMED — K survives** |
| DM3 effect-size | K∝θ², N_detect∝θ⁻⁴ | K(0.1)/K(0.03)=11.0≈11.1; **N_detect(θ=0.01)=5.6e7** | **CONFIRMED — sub-feasible at physical θ** |

**Verdict: FALL BACK to notion-2 ceiling.** Robust findings: the M_mem statistic HAS teeth (classical HMM
0.102, control 0); K∝θ²; the joint-parity twirl does NOT kill K. Two reasons the headline does not stand:
**(1) my toy quantum baths have M_mem≈0** — a single bath qubit + fixed coupling is NOT a genuine
memory-bearing non-Markovian bath (a MODEL inadequacy, not a physics law), so the headline conjunction
(K>0 ∧ M_mem>0) is UNDEMONSTRATED; **(2) effect-size cap (robust, model-independent):** at physical coherent
coupling θ=0.01, N_detect(K)=5.6e7 ≫ 1e6 — the coherence is sub-feasible at realistic strength.
⇒ **the quantum-dephasing headline does NOT cheaply stand; the dual-purpose claim (notion-2 plumbing = quantum
plumbing) is REFUTED.** The quantum headline needs a genuine memory-bearing quantum bath (pseudomode/GKSL —
a bigger, deferred build) AND must beat the effect-size cap — deferred, honestly reported. **notion-2
(classical multi-time memory) is the achievable, robust passive-record legitimacy signal; build it on its own
merit.** Honest limit: the toy's M_mem=0 does not PROVE a genuine quantum bath lacks record memory — it proves
THIS toy does; the fair test is the deferred memory-bearing-bath build.

## Epistemic classes

- **(a) exact:** DM1 K and M_mem from exact-DM / exact classical-HMM distributions; DM3 `θ²` scaling.
- **(b) band/finding:** DM2 joint-parity K-survival magnitude; DM3 feasible-N.
- **(c) declared:** minimal 1-system + 1-bath (+1-spectator for the parity) fixture; `M_S=σ_x` single-qubit
  and `X_S X_{S2}` two-qubit parity as stabilizer proxies (the full d3 multi-qubit stabilizer is the carrier
  build's stronger check, not this toy).
