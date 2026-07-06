# Reading note (精读): Bäcker, Palaparthy, Strunz, "Revealing the quantum nature of memory in non-Markovian dynamics on IBM Quantum" (arXiv:2510.19522)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → text via PyMuPDF
> (`arxiv.org/pdf/2510.19522`, 11 pages, v1, 22 Oct 2025; published NJP 28 (2026),
> IOP DOI 10.1088/1367-2630/ae5f3d). All §/Eq/quote refs transcribed from that text.
> Source URL: https://arxiv.org/abs/2510.19522
> **Adjudication target (Flag 0):** confirm the applied Bäcker-group witness uses the
> `C♯ < C` (entanglement-of-assistance / classical-memory-bound) form — NOT a bare
> revival — and extract EXACTLY how E♯ is computed, the measurement protocol (active
> single-time channel/Choi tomography vs passive multi-time record), and any d>2 /
> multi-qubit treatment. **Verdict: CONFIRMED on all points.** The witness is the
> assistance form (Eq. 3), computed as closed-form concurrences (d=2) or Fei/Chen
> bounds (d>2), from ACTIVE state tomography of an ancilla-coupled Choi state — a
> single-time dynamical-map object, explicitly NOT a passive multi-time record.

## Metadata [paper]

- **Authors:** Charlotte Bäcker, Krishna Palaparthy, Walter T. Strunz (TUD Dresden
  University of Technology, Institute of Theoretical Physics).
- **Venue / status:** arXiv:2510.19522v1 [quant-ph], 22 Oct 2025 → New J. Phys. 28
  (2026), DOI 10.1088/1367-2630/ae5f3d.
- **Type:** applied / experimental (IBM Quantum hardware realization of the
  Bäcker–Beyer–Strunz map-based quantum-memory criterion, PRL 132, 060402 = arXiv
  2310.01205; note that PRL vol/page here reads "132, 060402" — cross-ref our note
  `backer_local_disclosure_quantum_memory_2310.01205.md`).
- **Hardware:** `ibm_sherbrooke` (IBMQ Eagle processor), also confirmed qualitatively
  on `ibm_kyiv` and `ibm_brisbane`; local noise-model emulator `fake_sherbrooke`.

## Executive summary [paper]

Applied companion to the theory paper 2310.01205. Implements the map-based quantum-
memory criterion on real superconducting hardware via a **collision model**: the
open-system dynamics is a sequence of short unitary "collisions" between the system
qubit and a single environment qubit; an ancilla is Bell-entangled with the system
and left untouched so the time-evolved system–ancilla state IS the Choi–Jamiołkowski
state of the two-time dynamical map. They then **witness quantum memory by comparing
the concurrence of ASSISTANCE at an earlier time t1 to the concurrence of FORMATION
at a later time t2**: if `C♯(t1) < C(t2)` the memory cannot be classical (Eq. 3).

- **Single-qubit (Sec. III):** non-Markovian amplitude damping `γ_−(t)=tan(t)`
  (Eq. 4). Ideal theory gives the MAXIMAL gap `C♯(t1)=0 < 1=C(t2)`. On real
  `ibm_sherbrooke` (gδt=π/4, t1=2 collisions, t2=4 collisions) they measure
  `C♯(t1)=0.51 < 0.62=C(t2)` (Eq. 7) → quantum memory verified DESPITE noise
  (Choi fidelities 0.93 at t1, only 0.57 at t2). A lower-gate variant gδt=π/2 gives
  `C♯(t1)=0.39 < 0.77=C(t2)`.
- **Two-qubit (Sec. IV):** the physically-motivated 3-qubit generalization (Eq. 8)
  transpiles to >500 gates per collision → decoheres → NO quantum memory witnessed on
  hardware (nor on `fake_sherbrooke`). They fall back to a gate-cheap **toy** model
  (Fig. 5, Eq. 13: two DISJOINT two-qubit unitaries, system qubits never interact) and
  DO witness it: `C♯>(t1)=0.72 < 0.89=C<(t2)` (Eq. 14), using the d>2 bound criterion
  Eq. (10).

## Key equations/criteria [paper]

### Classical-memory definition (two-time), Eq. (1)

A two-time dynamics `D = (E_t1, E_t2)` is realizable with **classical memory** iff there
exist Kraus operators {K_i} and CPT maps Φ_i such that

```
E_t1[ρ] = Σ_i K_i ρ K_i†,
E_t2[ρ] = Σ_i Φ_i[ K_i ρ K_i† ].
```

Physical reading (verbatim): "First, at t = t1, a measurement on the system is performed
such that on average the map E_t1 is realized. Now, conditioned on the outcome i of this
measurement, a CPT map Φ_i is applied. ... Crucially, the measurement outcome i can be
stored in classical memory, and the subsequent evolution given by the conditioned CPT
map Φ_i can be realized with a new, uncorrelated environment." Otherwise the dynamics
"is said to require quantum memory."

### Choi–Jamiołkowski embedding, Eq. (2)

`ρ^{SA}_t = (E_t ⊗ 1_A)[ρ^{SA}_0]`, and for the maximally entangled
`ρ^{SA}_0 = |Φ+⟩⟨Φ+|` with `|Φ+⟩ ∼ Σ_j |jj⟩`, "ρ^{SA}_t is nothing but the
Choi-Jamiołkowski state corresponding to the map E_t."

### THE WITNESS — Eq. (3) (single-qubit / d=2)

```
C♯( ρ^{SA}_t1 )  <  C( ρ^{SA}_t2 )   ⇒   memory must be QUANTUM
```

Verbatim: "if we observe that the joint states ρ^{SA}_t1 and ρ^{SA}_t2 at times t1, t2
satisfy C♯(ρ^{SA}_t1) < C(ρ^{SA}_t2), where **C is the concurrence of formation and C♯
is the concurrence of assistance**, the memory has to be quantum and the dynamics cannot
be realized with classical memory." — **This is the E♯ < E entanglement-of-assistance
form (the '#' is retained), NOT a bare revival.** "Note that for a single qubit system,
when ρ^{SA} is a two-qubit state, there are closed-form expressions for both
concurrences."

### How E♯ is computed — d=2 (single qubit): CLOSED-FORM concurrences

- `C` = concurrence of formation (Wootters, ref. [69]) — closed form for 2-qubit states.
- `C♯` = concurrence of ASSISTANCE (DiVincenzo/Fuchs/... ref. [70]; Laustsen/Verstraete/
  van Enk ref. [71]) — closed form for 2-qubit states.
- No numerical convex-roof optimization is needed in the single-qubit case; both are
  evaluated directly from the reconstructed 2-qubit Choi state `ρ^{(n)}_SA`.
  (Contrast the theory paper 2310.01205: for zero-T AD the rank-2 Choi gives `C♯ = C`
  identically — that is the closed-form simplification that makes the single-qubit test
  cheap.)

### How E♯ is computed — d>2 (two-qubit → 3-qubit Choi): BOUNDS, Eqs. (10)–(12)

For the two-qubit dynamics the system–ancilla state is NOT a two-qubit state, so
"there is no closed-form expression for the higher-dimensional concurrence of formation
C or concurrence of assistance C♯ [82,83]." They instead use an UPPER bound on C♯ and a
LOWER bound on C, giving the still-sufficient witness

```
C♯>(t1)  <  C<(t2)        (Eq. 10)
```

with the explicit upper bound on concurrence of ASSISTANCE (ref. [84], Li–Fei–Albeverio–Liu)

```
C♯>  =  sqrt( 2 ( 1 − tr( tr_A(ρ_SA)^2 ) ) )        (Eq. 11)
```

i.e. built from the purity of the reduced state `tr_A(ρ_SA)`, and the lower bound on
concurrence of FORMATION (ref. [85], Chen–Albeverio–Fei)

```
C<  =  m̃ · max( ||(ρ_SA)^{T_S}|| − 1 ,  ||(ρ_SA)^{T_A}|| − 1 )        (Eq. 12)
```

with `m̃ = sqrt( 2 / (m(m−1)) )`, m = dimension of the smaller party, and `T_S/T_A` the
partial transpose w.r.t. system / ancilla (a computable-cross-norm / PPT-type / realignment
lower bound). So for d>2 the assistance quantity is a **purity-based analytic upper bound**,
NOT a numerical optimization; the formation quantity is a partial-transpose-norm lower bound.
(They also note the toy-model witness "can also be confirmed with respect to the entropic
witness introduced in Ref. [51]" [= 2310.01205 / entropic-witness companion], "which is
also suitable to characterize memory in higher-dimensional quantum dynamics.")

### Measurement / experimental protocol — ACTIVE single-time channel/Choi tomography

- Circuit (Fig. 2): system+ancilla prepared in a Bell state; environment qubit init |0⟩;
  the two-qubit collision unitary `U_δ` (Eq. 5) applied n times; **then quantum STATE
  tomography on the system–ancilla state** `ρ^{(n)}_SA`.
- "Assuming that the ancilla is isolated from the environment, the system-ancilla states
  ρ^{(n)}_SA can be used to reconstruct the quantum map with the help of the
  Choi-Jamiołkowski isomorphism." → This is a **physical realization of the CJ
  isomorphism**: the tomographed object IS the single-time dynamical map's Choi state.
- Shots: single-qubit = 9 tomography settings × 4096 shots = 36,864 runs per circuit,
  N+1=11 circuits (n=0..10). Two-qubit generalization = 27 settings; toy model = 81 (+2
  readout-mitigation) settings, run to t1 and t2 separately.
- The witness reads the map at TWO chosen times (a two-time dynamics D=(E_t1,E_t2)),
  each obtained by its OWN full state-tomography reconstruction. This is an ACTIVE,
  interventionist characterization (prepare maximally-entangled probe → evolve → tomography),
  **NOT a passive record of a freely-running process.**

### Passive multi-time records / process tensors — explicitly the road NOT taken

- Verbatim (Intro): "Many approaches use the powerful framework of process tensors [43,56,61]
  as they carry the maximal possible information about the dynamics. Experimental advances
  using IBMQ have shown that obtaining a (restricted) process tensor for the classification
  of the memory is expensive and can so far be used to investigate single-qubit dynamics
  only [61]. The aim of this article is to simulate non-Markovian dynamics and to witness
  the quantumness of the memory **with a criterion based only on the dynamical map [51]**...
  less expensive experimentally."
- Verbatim (Sec. II): "The advantage of considering maps at distinct times instead of
  process tensors lies in the comparably low experimental effort to obtain the relevant
  information [61,66]."
- Verbatim (Conclusions): "numerical investigations of the spin boson model have shown
  that the **process tensor, which contains more information than a combination of two
  quantum maps, is more sensitive in detecting quantum memory [60].** It may therefore be
  interesting to challenge contemporary quantum computers to implement full or reduced
  process tensor tomography in the two-qubit case and diagnose quantum memory from suitable
  multi-time quantities." → i.e. the passive/multi-time-record object is acknowledged as
  STRICTLY MORE POWERFUL but is left as future work; this paper's witness lives on the
  single-time (two-time-map) active-tomography object.

## Relevance to project [ours]

**Flag 0 (revival ≠ quantum) — CONFIRMED.** This applied paper cements the same message
as the theory paper: the CORRECT witness carries the '#'. The bare quantity that a plain
negativity/concurrence REVIVAL fires on is only the RHP/BLP non-Markovianity witness
`C(t2) > C(t1)` (ref. [63], the "increase in entanglement with an ancilla" criterion the
paper explicitly labels merely "a sufficient criterion for ... CP-indivisible" — Sec.
III.B.1). The quantum-memory upgrade REQUIRES comparing against the classical-memory
BOUND `C♯(t1)` (entanglement of assistance = the most entanglement a classical-memory
realization could have handed forward). `[ours]` Our in-house Control 0b (classical RTN
dephasing firing a bare negativity-revival witness) is exactly the "CP-indivisible but
still classical-memory" regime this paper separates: a bare revival witnesses
non-Markovianity/memory, the `C♯ < C` gap witnesses QUANTUM memory. Our dropped-'#'
"Control 3b" was the bare-revival mistake; Eq. (3)/(7)/(14) here are the corrected tool.

**Flag 1 (is quantum memory expressed on the PASSIVE syndrome record?) — this paper says
NO for its own witness; the answer is ACTIVE-tomography-only.** `[paper]` The witness is
computed from a Choi state obtained by ACTIVE state tomography of a Bell-prepared
system+ancilla under an interventionist collision circuit — a single-time dynamical-map
object. `[paper]` The paper EXPLICITLY flags that the passive/multi-time process-tensor
object is more sensitive (ref. [60], spin-boson) but is NOT what they use, because it is
experimentally expensive. `[ours]` Therefore, for our QEC-simulator setting, the direct
implication is: **`C♯ < C` as stated is a witness on an ACTIVE channel-tomography object,
not on our PASSIVE syndrome record.** To claim quantum memory is EXPRESSED on the passive
multi-time record we need the process-tensor / multi-time quantum-memory witness (the
Giarmatzi–Costa [56], Taranto–Milz [58], or the spin-boson process-tensor [60] line the
paper cites but defers), and to check that our passive syndrome record actually contains
the requisite multi-time correlations (our standing concern that the passive record may
be information-lossy vs the active Choi object). `[ours]` This paper is thus the CORRECT
single-qubit (and toy 2-qubit) template for the ACTIVE witness, but it does NOT
demonstrate a passive-record witness — Flag 1 remains OPEN and points at the process-tensor
references, not at this map-based criterion.

**d>2 / collective / multi-qubit — partially covered, with a hard hardware caveat.**
`[paper]` The criterion generalizes to d>2 via the Fei/Chen bounds (Eqs. 10–12), and they
do witness a 2-qubit TOY dynamics on hardware. BUT the physically-motivated 2-qubit
collective dynamics (Eq. 8, a shared single-qubit environment coupling both system qubits
— structurally close to our shared-mode collective-emission target) FAILED to witness
quantum memory on hardware: >500 gates/collision, decoherence washes it out, `C♯` stays
≈const ("close to random unitary dynamics ... almost no quantum memory"). `[ours]` The toy
that DID work (Eq. 13) is a PRODUCT of two disjoint 2-qubit unitaries with NO system–system
interaction — i.e. it deliberately removes the collective coupling to save gates. So the
paper does NOT deliver a hardware witness for genuinely collective/shared-bath 2-qubit
memory; it delivers the analytic bound-criterion plus a factorized toy. For our collective
σ− shared-mode question, the analytic `C♯> < C<` bound is the usable tool, but this paper
provides no collective-channel demonstration to lean on.

## Decisive verbatim quotes [paper]

- (Sec. II, the criterion) "if we observe that the joint states ρ^{SA}_t1 and ρ^{SA}_t2
  at times t1, t2 satisfy C♯(ρ^{SA}_t1) < C(ρ^{SA}_t2), where C is the concurrence of
  formation and C♯ is the concurrence of assistance, the memory has to be quantum and the
  dynamics cannot be realized with classical memory."
- (Sec. III.B.1, distinguishing bare-revival from the witness) "there is an increase in
  concurrence and hence entanglement with the ancilla reflecting the non-Markovian nature
  of the dynamics. This is also a sufficient criterion for the dynamics D = (E_t1, E_t2)
  to be CP-indivisible." — i.e. bare revival ⇒ only CP-indivisibility (non-Markovianity),
  NOT quantum memory.
- (Eq. 7, the single-qubit result) "C♯(t1) = 0.51 < 0.62 = C(t2). Hence, the quantumness
  of the memory ... can be verified via Eq. 3."
- (Sec. IV.A, d>2 has no closed form) "there is no closed-form expression for the
  higher-dimensional concurrence of formation C or concurrence of assistance C♯ [82,83].
  However, considering a suitable upper bound C♯> for C♯ [84] and lower bounds C< for C ...
  one arrives at the condition C♯>(t1) < C<(t2)."
- (Eq. 11) "C♯> = sqrt( 2 (1 − tr( tr_A(ρ_SA)^2 )) ), as upper bound for the concurrence
  of assistance."
- (Sec. III.B, protocol) "we initialize system and ancilla in a maximally entangled Bell
  state and leave the ancilla untouched afterwards. ... After each of the N + 1 circuits we
  perform quantum state tomography of the system-ancilla state ρ^{(n)}_SA."
- (Conclusions, process tensor deferred) "the process tensor, which contains more
  information than a combination of two quantum maps, is more sensitive in detecting
  quantum memory [60]. It may therefore be interesting to challenge contemporary quantum
  computers to implement full or reduced process tensor tomography in the two-qubit case
  and diagnose quantum memory from suitable multi-time quantities."

## Tags

- `[paper]` witness Eq. (3): `C♯(t1) < C(t2)` — concurrence of assistance below concurrence
  of formation ⇒ quantum memory required (the '#'/assistance form, NOT a bare revival).
- `[paper]` d=2: closed-form concurrence (Wootters [69]) + concurrence of assistance
  ([70,71]); no numerical optimization.
- `[paper]` d>2: bound criterion Eq. (10) `C♯>(t1) < C<(t2)`; C♯> = purity-based upper bound
  (Eq. 11, [84]); C< = partial-transpose-norm lower bound (Eq. 12, Chen–Albeverio–Fei [85]).
- `[paper]` protocol = ACTIVE quantum state tomography of a Bell-prepared ancilla-coupled
  Choi state (single-time dynamical map), on `ibm_sherbrooke`; NOT a passive record.
- `[paper]` process tensor / multi-time record acknowledged as STRICTLY more sensitive
  ([60]) but explicitly deferred as future work.
- `[paper]` physically-motivated COLLECTIVE 2-qubit dynamics (Eq. 8) FAILED on hardware;
  the witnessed 2-qubit toy (Eq. 13) is a factorized product with no system–system coupling.
- `[ours]` Flag 0 CONFIRMED: revival = non-Markovianity/CP-indivisibility; `C♯ < C` = quantum
  memory. Our dropped-'#' control witnessed only memory.
- `[ours]` Flag 1: this witness lives on the ACTIVE channel-tomography object, NOT the passive
  syndrome record; passive-record quantum memory ⇒ need the process-tensor witnesses this
  paper defers. Flag 1 stays OPEN.
