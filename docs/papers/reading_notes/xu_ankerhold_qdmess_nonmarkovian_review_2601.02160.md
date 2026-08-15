# Body review — Xu, Vadimov, Stockburger, Ankerhold, "Simulating Non-Markovian Dynamics in Open Quantum Systems"

## Provenance
- **Source:** arXiv:2601.02160v2 (Jan 2026), Colloquium-style review (Ulm / Aalto); fetched
  2026-07-02, cached `outputs/papers/2601.02160.{pdf,txt}` (28 pp).
- **Reading method:** BODY-READ (declared level, HANDOFF §4.6): abstract, ToC, Sec. I
  intro, Fig. 1 taxonomy, Sec. XII Summary read; method sections II–XI not worked through.
  Keyword sweep: `syndrome` 0 hits; `learn` 3 hits (none a learning protocol) — this is a
  SIMULATION-methods review, no estimation/learning content, no QEC content.
- **Why now:** user-caught coverage gap (engine-landscape adjacency for our
  pseudomode-embedding choice in the coupled-teacher line).

## Executive summary
Unifying review of the non-Markovian open-system SIMULATION method zoo — HEOM,
Lindblad-pseudomodes, chain mappings (TEDOPA), quantum-Brownian-motion master equations,
stochastic unravelings (SLN, HOPS), thermofield methods, perturbative treatments — under
one umbrella: **QD-MESS** (quantum dissipation in minimally extended state space),
time-local equations on system ⊕ few effective reservoir modes. Central object = the
reservoir spectral noise power S_β(ω) = −2 Im{κ†G(ω)η} with a Green's-function
decomposition; the **invariance of S_β(ω) under linear transformations of reservoir mode
space** generates the equivalences between the named methods (each method = one choice of
mode representation of the same kernel). Verdict of the review: embedding/hybrid methods
beat both reduced-space and full-Hilbert-space approaches on applicability, stability, and
cost; Table I summarizes the trade-offs.

## Relevance to the coupling simulator
1. **The citable umbrella for our engine choice.** Our coupled-pseudomode pilot
   (`outputs/coupled_pseudomode_pilot_v1_n2.py`, per 2506.10308) sits in their
   Lindblad-pseudomode box; this review is the standard recent citation that the
   pseudomode embedding is one exact member of an equivalence class of kernel-faithful
   embeddings (satisfies the citation recency policy; supersedes reaching for the older
   single-method papers as landscape citations).
2. **Their invariance ≠ our gauge — keep the distinction sharp in prose.** Their
   mode-space invariance is a REPRESENTATION gauge on the ENGINE side: different extended
   state spaces, same S_β(ω), same reduced dynamics. Our record gauge is an OBSERVATION
   gauge: different Σ (different physical kernels!), same detector-record law at the
   declared moment order. One sentence in the paper draft may cite the contrast; never
   conflate them.
3. **No ownership contact.** No learning, no estimation, no records, no QEC, no
   identifiability content — zero overlap with Bones B/#2/#3 claims.
4. **Future use.** If the coupled-teacher engine is ever challenged on embedding choice,
   Table I is the neutral arbiter to cite for "pseudomode vs HEOM vs chain" cost/stability
   trade-offs at our kernel class.

## Trust
Body-read only — cite for taxonomy/landscape statements; re-read the relevant method
section before relying on any specific equation.
