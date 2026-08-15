# Reading note (精读): Milz et al., "When Is a Non-Markovian Quantum Process Classical?"

Provenance: FULL-TEXT read (all substantive sections I-VIII + Example 1 + theorem proofs
read in the body). Source: `outputs/papers/1907.05807.txt` (42-page arXiv v3 conversion,
`===== PAGE N =====` markers cited below). Adjudication target: does this result "own" the
classicality of QEC-stabilizer / syndrome records? **Verdict up front: NO — they never
instantiate their framework on QEC / stabilizer / syndrome records; they treat generic
single-observable sequential projective measurements.**

## Metadata [paper]

- Title: "When is a non-Markovian quantum process classical?" (PAGE 1).
- Authors: S. Milz, D. Egloff, P. Taranto, T. Theurer, M. B. Plenio, A. Smirne, S. F. Huelga.
- Venue: PRX 10, 041049 (2020); arXiv:1907.05807v3 [quant-ph], dated "August 12, 2020" (PAGE 1).
- Lineage: extends Ref. [33] (Smirne/Egloff/Huelga et al., the Markovian coherence<->classicality
  result) to the **non-Markovian** case using the quantum-comb / process-tensor framework
  ([35,36,37,38]).
- Object of study (PAGE 1): "temporal processes which are probed sequentially by means of
  projective measurements of the same observable."

## Executive summary [paper]

The paper gives an operational definition of when a temporal quantum process is "classical":
the family of multi-time joint outcome probabilities obtained by sequentially probing the system
must satisfy the **Kolmogorov consistency conditions**. If they do, "there is therefore nothing
inherently quantum about the observed phenomenon" (PAGE 1); if they do not, no underlying classical
stochastic process reproduces the statistics and the process is non-classical. This condition is a
non-invasiveness / Leggett-Garg-type criterion.

Three results carry the paper:
1. **Markovian case (Theorem 1):** a Markovian process is classical iff it can be modeled by a
   diagonal initial state and **non-coherence-generating-and-detecting (NCGD)** propagators —
   coherence may be created but cannot be detected later. (Reiterates/generalizes Ref. [33].)
2. **Key non-Markovian finding:** with memory, absence of system coherence is **necessary but NOT
   sufficient** for classicality. Example 1 exhibits a process that never has coherence in the
   measured basis yet violates Kolmogorov consistency. The right invariant becomes **quantum
   discord** between system and environment (Theorems 3/4, NDGD dynamics).
3. **Genuinely quantum processes (Sec. VII):** with memory there exist processes non-classical
   under *every* (non-trivial, fixed-in-advance) measurement scheme — impossible in the memoryless
   case.

They also derive an experimentally/computationally accessible non-classicality measure `M(C)` via
a linear program, with a two-time upper bound.

## Method (deep) [paper] — exact definitions and equations (verbatim fragments)

### 1. Classicality = Kolmogorov consistency (the CORE definition this note adjudicates)

The classicality criterion is marginalization-consistency of the joint outcome distributions.
Eq. (1)/(9), the **Kolmogorov consistency condition** (PAGE 2, restated PAGE 4):

```
P_{n-1}(x_n,t_n; ... ; [omit x_j,t_j] ; ... ; x_1,t_1)
   = sum_{x_j} P_n(x_n,t_n; ... ; x_j,t_j; ... ; x_1,t_1)    for all n <= K, for all j.
```

Verbatim, the condition is that marginalizing over an intermediate outcome reproduces the
lower-order distribution: "the probability distributions for all subsets of times can be obtained
by marginalization" (PAGE 4). And the classicality verdict: "If these satisfy the Kolmogorov
consistency conditions ... then they can, in principle, be explained by a fully classical model"
(PAGE 1); "there is therefore nothing inherently quantum about the observed phenomenon" (PAGE 1).

Definition 1 (K-classical process, PAGE 5, verbatim): a process "is said to be K-classical if the
Kolmogorov consistency conditions of Eq. (9) are satisfied up to n = K."

Interpretation as non-invasiveness (PAGE 5, verbatim): "the Kolmogorov consistency conditions in
Eq. (9) are in fact a statement of the non-invasiveness of the performed measurements: if they
hold true, then not performing a measurement ... cannot be distinguished ... from averaging over
their probabilities." Underlying assumptions (PAGE 4, verbatim): "the assumptions of realism per
se ... and the possibility to implement non-invasive measurements."

### 2. Markovianity (separate from classicality)

Eq. (2)/(13), K-Markovianity (PAGE 3 / PAGE 7, verbatim): `P(x_n|x_{n-1},...,x_1) = P(x_n|x_{n-1})
for all n <= K`. Note: Markovianity is basis-dependent and distinct from classicality.

### 3. Markovian characterization — NCGD (Theorem 1)

Completely dephasing map `Delta` (Eq. (20), PAGE 8, verbatim): `Delta[rho] = sum_{x_j}
<x_j|rho|x_j> |x_j><x_j|`. NCGD condition (Eq. (3)/(21), PAGE 2 / PAGE 8):

```
Delta o Lambda_{t_{j+1},t_j} o Delta o Lambda_{t_j,t_{j-1}} o Delta
   = Delta o Lambda_{t_{j+1},t_j} o Lambda_{t_j,t_{j-1}} o Delta   for all j.
```

Theorem 1 (PAGE 8-9, verbatim): a K-Markovian process "is also K-classical ... if and only if
there exist a system state rho_{t0} ... which is diagonal in the computational basis ... and a set
of propagators ... which are NCGD." Intuition (PAGE 2, verbatim): NCGD "maps that ... can create
coherences, but not in a way that can be detected at a later time."

### 4. Non-Markovian characterization — quantum combs (Theorem 2 / 2')

Multi-time probabilities from a **quantum comb** `C_K` (Eq. (4), PAGE 2): `P_K(x_K,...,x_1) =
C_K[P_{x_K},...,P_{x_1}]`, with `P_{x_j}[rho] = <x_j|rho|x_j> |x_j><x_j|`. General
system-environment form (Eq. (11), PAGE 6): the joint distribution is `tr[(P_{x_n} (x) I_e) o
U_{t_n,t_{n-1}} o ... o (P_{x_1} (x) I_e) o U_{t_1,t_0}[eta^{se}_{t0}]]`.

Theorem 2 (K-classical combs, PAGE 13, verbatim): a comb yields a K-classical process iff, for all
`T' subset of T`, letting the comb act on identity maps at times in `T'` equals letting it act on
completely dephasing maps `Delta_j` there (Eq. (42)). "a general process is K-classical iff
measurements in the computational basis cannot distinguish the action of completely dephasing maps
from the action of identity maps" (PAGE 13). Theorem 2' recasts this on the Choi state (PAGE 13).

### 5. Discord characterization — NDGD (Theorems 3, 4)

NDGD dynamics (Def. 3, Eq. (68), PAGE 19-20, verbatim): system-environment maps `{Gamma}` with
`Delta_{j+1} o Gamma_{t_{j+1},t_j} o Delta_j o Gamma_{t_j,t_{j-1}} o Delta_{j-1} = Delta_{j+1} o
Gamma_{t_{j+1},t_j} o I_j o Gamma_{t_j,t_{j-1}} o Delta_{j-1}` where `Delta_k` act on the system
alone. Theorem 3 (PAGE 20, verbatim): the process "is K-classical if the initial
system-environment state eta^{se}_{t0} and the set {Gamma} of maps ... are zero discord and NDGD,
respectively." Zero-discord initial state (PAGE 3, verbatim): `eta^{se}_{t0} = sum_m p_m
|x_m><x_m| (x) xi_m`. Theorem 4 (PAGE 20): NDGD is sufficient but not necessary; however any
K-classical process **admits an NDGD dilation** ("for every K-classical process there is an NDGD
dilation that reproduces it correctly", PAGE 21).

## The MECHANISM [paper -> ours]

[paper] The mechanism producing non-classicality is **detectable measurement invasiveness carried
by memory**: even when the reduced system state is diagonal in the measured basis at all times
(zero coherence), correlations with an inaccessible environment (discord) can be created and later
detected by the sequential measurements, breaking Kolmogorov consistency. Formally: "in general we
can have Delta[rho^s_{tj}] = I[rho^s_{tj}] for all tj, without it implying Delta (x) I_e
[eta^{se}_{tj}] = I[eta^{se}_{tj}] for all tj" (PAGE 10) — dephasing the system does not dephase
the joint state, so measurements remain invasive.

[ours] This is the exact abstract shape of our non-Markovian coupling program (see MEMORY:
"Non-Markovian wedge MUST be coherence" and "Coupling: non-Markovian IS the contribution"): a
system coupled to a bath where the memory lives in system-environment correlations. But note the
mismatch that decides the adjudication (below): their "measurement" is a **projective read of the
SAME single system observable at every time**, not a stabilizer/syndrome extraction round.

## The OBSERVABLE / metric [paper]

Non-classicality measure `M(C)` (PAGE 16, Eqs. (54)-(56)): defined operationally via an
Alice/Bob/Rudolph guessing game — `P_B(C) = (1/2)(1 + M(C))` — where `M(C)` is half the solution
of a min-max over classical-comb approximations and projective test sequences (Eq. (55)),
reformulated as a **linear program** (Eq. (56)). Properties (PAGE 16, verbatim): "M(C) is
faithful, i.e., its value is zero if the statistics is classical." Two-time upper bound (Eq. (57),
PAGE 17, verbatim): `M(C) <= | sum_{x2} P(x2) - sum_{x1} P(x2,x1) |` — the "natural quantifier of
non-classicality" used in Leggett-Garg-type scenarios. The measure is claimed experimentally
accessible from existing data ("could be evaluated based on already existing experimental data",
PAGE 2; explicitly the quantum-walk data of Ref. [51], PAGE 17).

Measurement setting (PAGE 6, verbatim, load-bearing): "we will analyze the classicality of a
process based on the joint probability distributions obtained from sequential sharp measurements in
a fixed basis" with `P_x[rho] := |x><x| rho |x><x|` (Eq. (10)). They restrict to "orthogonal
rank-1 (sharp) projectors" (PAGE 6) and invoke repeatability: "two sequential measurements (without
any evolution in between) would give the same value with unit probability" (PAGE 6).

## Findings + numbers [paper]

1. Markovian: classical <=> diagonal initial state + NCGD propagators (Theorem 1, PAGE 9). No
   numbers — structural iff.
2. **Absence of coherence is necessary but NOT sufficient with memory** (verbatim, PAGE 1): "the
   absence of coherence does not guarantee the classicality of observed phenomena." Example 1
   (PAGE 10-11): qubit coupled to a continuous mode, `U_{t_j,t_i}|l,p> = e^{i phi_l p (t_j - t_i)}
   |l,p>`; with a Lorentzian bath `k(t) = e^{-2 Gamma |t|}` "no coherence w.r.t. sigma_x will be
   generated" (PAGE 11) yet "the statistics resulting from measurements in the {|+>} basis is
   non-classical" (PAGE 11). This is the headline finding for us.
3. Discord is the correct invariant: classical <=> (there exists) zero-discord state + NDGD
   dilation (Theorems 3/4). "violation of a Leggett-Garg inequality implies that quantum discord
   must have been created (and later detected)" (PAGE 24).
4. Classical processes are **measure zero** in the set of all combs (PAGE 15, verbatim: "combs
   leading to classical processes are of measure zero in the set of all combs").
5. Genuinely quantum processes exist (Sec. VII): non-classical under every non-trivial fixed
   measurement scheme; possible **only** with memory (PAGE 24, verbatim: "This can happen only for
   non-Markovian processes").

## Limitations [paper]

- **Basis / measurement-scheme dependence** (PAGE 5, verbatim): "the classicality of a process
  according to the above definition depends upon the manner in which the system of interest is
  probed." Classicality is a per-observable statement.
- NDGD is sufficient, not necessary (Appendix H example; PAGE 20: "it is not a necessity for
  classical statistics that the corresponding maps are NDGD").
- Deciding K-classicality in the non-Markovian case requires the **full comb** on the probed times,
  not just pairwise propagators (PAGE 15).
- Restricted to **finite K** and finite outcome sets (Definition 1, PAGE 5).
- Restricted to **sharp rank-1 projective measurements of a fixed observable** (PAGE 6); the
  discord connection is lost if one leaves this measurement class (PAGE 24).
- The onset of macroscopic classicality (a temporal analog of decoherence-induced pointer bases)
  is left as an open problem (PAGE 25, Outlook).

## Relevance [ours]

Adjudication of "does this own the classicality of QEC stabilizer / syndrome records": **NO.**

Term search over the full text (case-insensitive):
- "stabilizer" — **absent** (0 matches).
- "syndrome" — **absent** (0 matches).
- "error correction" / "error-correction" / "quantum error" / "fault-toler*" — **absent** (0
  matches).
- "code"/"codes" — **absent** as QEC nouns (0 matches).
- "Pauli" — 2 matches, both merely naming the `sigma_z` / `sigma_x` operator of the single toy
  qubit in Example 1 (PAGE 10, PAGE 24). Not a code / stabilizer usage.
- "surface" — absent.

What their measurement setting actually is (verbatim, PAGE 1): "probed sequentially by means of
projective measurements of the **same observable**"; and (PAGE 6) "sequential sharp measurements in
a fixed basis {|x>}". This is a single-observable Leggett-Garg-style temporal-correlation setup on
one system, NOT a stabilizer measurement record (which reads *many commuting* stabilizer
observables per round, ancilla-mediated, with a code space). They never instantiate a code, a
stabilizer group, an ancilla-extraction circuit, or a syndrome stream. Example 1 is a single qubit
+ one continuous bath mode.

Why this still matters to us (the honest positive):
- Their **Kolmogorov-consistency = classicality** criterion is exactly a rigorous, field-standard
  formalization of "when is a temporal record explainable by a classical stochastic process." Our
  syndrome / detection-event records ARE families of multi-time binary distributions; asking
  whether a Markov-order-k classical model reproduces them is a Kolmogorov-consistency question in
  spirit. This paper is the reference for that framing (and connects it to Leggett-Garg / discord).
- Their central negative — **no-system-coherence does NOT imply classical statistics under memory**
  — directly supports our MEMORY line "Non-Markovian wedge MUST be coherence": it says even a
  perfectly dephased (populations-only) system can produce non-Kolmogorov multi-time statistics via
  system-environment discord. This is a caution that a diagonal/incoherent reduced channel can
  still be non-classical at the multi-time level — relevant to whether classical Markov-k models
  can ever fully capture a memory-ful bath.
- But it does NOT do the QEC-specific work: it does not treat many-observable-per-round stabilizer
  measurement, does not connect to DEM/decoder records, and does not establish that our specific
  bath-coupled syndrome stream is classical or not. The claim "our correlated syndrome record is
  (non-)classical" is NOT owned by this paper.

## How to use / trust [ours]

- **Cite for**: the operational classicality-of-a-temporal-process definition (Kolmogorov
  consistency = non-invasiveness = Leggett-Garg), the comb-level characterization (Theorem 2),
  the discord invariant (Theorems 3/4), and — most usefully — the **coherence-absent-yet-
  non-classical** fact (Example 1) as prior art that motivates coherence/CP-divisibility as the
  unforgeable non-Markovian signature.
- **Do NOT cite for**: any claim about stabilizer/syndrome-record classicality, QEC decoding,
  Pauli-DEM reducibility, or that syndrome streams are/aren't classical. The paper is silent on
  QEC; instantiating its framework on a stabilizer record is *our* work, not theirs, and would be
  a non-trivial extension (multi-observable-per-round, ancilla-mediated, code-space measurements —
  outside their sharp-single-observable class, where they explicitly note the discord connection is
  lost, PAGE 24).
- **Trust level**: theorems are exact structural iff-statements (Theorems 1, 2, 2', 4) with proofs
  in-body/appendix; Theorem 3 is a one-directional sufficient condition (NDGD => classical);
  Example 1 is an exact analytic toy. `M(C)` faithfulness is proven from the game construction. All
  usable as (a)-class exact references for the DEFINITIONS; any application to our syndrome records
  is (b)/(c)-class until we build and verify the mapping ourselves.
- **Bridge task if we pursue it**: to actually use this on QEC records we would need to (i) fix the
  "observable" as the per-round detector/syndrome vector, (ii) check whether the sharp-projective
  single-observable assumption survives multi-stabilizer rounds, and (iii) recast Kolmogorov
  consistency as a Markov-order test on the detection-event distribution. That is a pre-registration
  of its own, not something this paper already delivers.

---
Summary (for the requesting agent):
- (a) Classicality criterion = the family of multi-time joint outcome distributions satisfies the
  **Kolmogorov consistency conditions** (Eq. (1)/(9): marginalizing over an intermediate outcome
  reproduces the lower-order distribution) — i.e. measurement non-invasiveness / Leggett-Garg
  realism.
- (b) Measurement setting assumed = **sequential sharp rank-1 projective measurements of the SAME
  fixed observable** (fixed computational basis) at multiple times on one system (`P_x[rho] =
  |x><x| rho |x><x|`, PAGE 6).
- (c) Do they treat stabilizer / syndrome / QEC records anywhere? **NO.** Zero matches for
  stabilizer, syndrome, error correction, quantum error, code; "Pauli" only names the sigma_z/x of
  the single-qubit toy (Example 1). Framework is generic single-observable temporal measurement;
  QEC is never instantiated.
