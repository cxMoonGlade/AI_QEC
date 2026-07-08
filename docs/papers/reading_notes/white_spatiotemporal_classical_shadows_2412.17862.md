# Reading note (精读): White et al., "Practical learning of multi-time statistics in open quantum systems" (arXiv:2412.17862)

> **Provenance (2026-07-05): FULL-TEXT read (精读), key sections.** PDF → txt
> `outputs/papers/2412.17862.txt` (31 pages). All §/Eq refs from that text.
> Also known as "Spatiotemporal Classical Shadows."
> Adjudication target: does this provide a practical method for LEARNING whether a
> multi-time process is classical vs quantum? **Verdict: YES — it provides classical-shadow
> protocols for process tensor estimation, but at single-qubit/small-system scale, not
> yet at QEC-register scale.**

## Metadata [paper]
- **Authors:** G.A.L. White (FU Berlin), L.C.L. Hollenberg (Melbourne), C.D. Hill (Melbourne/SQC),
  K. Modi (Monash/SUTD)
- **Venue / status:** arXiv:2412.17862 (Dec 2024). Preprint.
- **Type:** method (randomized measurement protocols for process tensor estimation)

## Executive summary [paper]
Applies randomized-measurement (classical shadow) protocols to the **process tensor** —
the Choi state on a multipartite Hilbert space over multiple time steps. Key insight:
non-Markovian dynamics distribute temporal correlations as **spatial correlations
between different legs of the process tensor**, which can be probed with few-body
observables via classical shadows. Distinguishes **classical non-Markovian** (process
tensor = convex combination of CPTP maps with POSITIVE amplitudes) from **quantum
non-Markovian** (amplitudes may be negative or complex). Central finding: **causality
constraints impose a learnability gap** — temporal correlations tend to be high-weight,
making them harder to probe with classical shadows than spatial correlations of the
same strength.

## Key results for K-survival [paper → ours]

### 1. Process tensor as spatial correlations
The process tensor T_{n:0} is a multipartite state over 2n "legs" (input + output at
each time). Non-Markovian temporal correlations = spatial correlations between different
time-leg pairs. Classical shadows can estimate k-body correlations with poly(k) sample
complexity.

### 2. Classical vs quantum non-Markovianity
A process tensor is **classically non-Markovian** if it can be expanded as:
T = Σ_μ α_μ C_μ where α_μ ≥ 0 and each C_μ is a product of CPTP Choi states.
If any α_μ < 0 or complex ⇒ **quantum non-Markovianity.**

### 3. Learnability gap
Causality (past doesn't depend on future) enforces that temporal correlations in the
process tensor are **high-weight** (involve many time-legs) → harder to learn with
classical shadows than spatial correlations. This means process tensor classicality
certification at QEC-register scale faces a fundamental sample-complexity barrier.

## Relevance to project [ours]
- **Methodological:** classical shadow protocols could be adapted to estimate the
  process tensor of joint-parity syndrome records, providing a K-like diagnostic
  without full process tomography
- **The learnability gap is a warning:** certifying K > 0 on a 2-data-qubit +
  ancilla + pseudomode system may be feasible; scaling to full surface-code registers
  faces this barrier
- **The α_μ sign criterion** (negative/complex α_μ = quantum) is an alternative to
  K for certifying quantum non-classicality that may be more directly accessible
  from shadow estimates

## Limitations
- Method-focused; no QEC or stabilizer-measurement instantiation
- Sample complexity for high-weight temporal correlations may be prohibitive at scale
- Requires randomized measurement capability not available in standard QEC circuits

## Tags
- `[paper]` classical shadows for process tensor = practical multi-time estimation
- `[paper]` α_μ ≥ 0 ↔ classical; α_μ < 0 or complex ↔ quantum non-Markovian
- `[paper]` learnability gap: temporal correlations are high-weight (harder to probe)
- `[ours]` potential alternative to K for certifying quantumness of syndrome records
