# Full-text note (精读, main text via ar5iv) — Giarmatzi & Costa, "Witnessing quantum memory in non-Markovian processes" (arXiv:1811.03722; Quantum 5, 440 (2021))

> **Provenance (2026-07-06): 精读 of the ar5iv HTML full text** (main text + the operational
> witness construction + SDP; appendices on the multi-time / n-step generalization skimmed).
> Source: https://ar5iv.labs.arxiv.org/abs/1811.03722 . This is **PAPER 3 of the Flag-#1
> literature-closure arc** — the process-tensor QUANTUM-memory witness. The mission question:
> does this witness separate quantum from classical memory (yes), and — decisively for our
> Flag #1 — does it read a PASSIVE syndrome record or require ACTIVE interventions? Sibling arc
> notes: the Bäcker E#[χ1]<E[χ2] assistance criterion (2310.01205) and the RTN backflow-forgery
> control. Related in-repo: `kam_nonmarkovian_surface_code_2410.23779`,
> `time_invariant_process_tensors_2603.06840`, `ace_process_tensor_toolkit_2405.19319`.

## Why load-bearing [ours]
Our settled result: **negativity/entanglement revival (backflow) of a reduced channel = RHP
non-CP-divisibility = non-Markovianity, and it is FORGEABLE by classical non-Markovian noise**
(Control 0b: classical RTN dephasing fires a bare negativity-revival witness while the genuine
Bäcker C#(t1)<C(t2) stays silent). We need a tool that certifies *quantum* memory, not mere
memory. This paper supplies exactly that at the **process-matrix / process-tensor** level:
quantum memory ⟺ *entanglement* of the process matrix across the A_I | A_O B_I temporal cut,
detected by a witness that is positive on every classical-memory process. It is the multi-time
generalization of "revival ≠ quantum." **BUT** — and this is the Flag-#1 verdict — the witness
is defined on a process matrix reconstructed by **active local instruments** (CP maps applied
at each measurement station, with the output of one time fed forward into the next). It is NOT
a functional of a passive sequence of measurement outcomes. See "Relevance to project" below.

## Metadata [paper]
- **Authors:** Christina Giarmatzi, Fabio Costa.
- **Venue:** Quantum 5, 440 (2021); arXiv:1811.03722.
- **Object:** the **process matrix / process tensor** W (a.k.a. superprocess) — a multi-time
  generalization of a quantum channel that encodes all system-environment correlations across a
  sequence of "measurement stations" A, B, … . Framework = operator (Choi) representation of
  the process, à la Costa–Shrapnel / Pollock et al. process tensor.
- **Contribution:** a *quantum-memory* witness (Hermitian operator Z) plus an SDP hierarchy
  (PPT → Doherty/DPS levels) that certifies temporal **entanglement** of W, thereby separating
  quantum memory from classical memory — a strictly finer distinction than Markov vs non-Markov.

## Executive summary [paper]
The process is sliced into "measurement stations" A, B, … . At each station an experimenter
**intervenes** on the system via a completely positive (CP) map / instrument; each station has
an *input* wire (A_I) and an *output* wire (A_O). The joint outcome statistics factor through a
single operator W via the generalized Born rule (Eq. below). Three nested classes:
- **Markovian:** W = ρ^{A_I} ⊗ T^{A_O B_I} ⊗ … — a tensor product of the initial state and the
  channel Choi matrices; the environment carries **no** memory between interactions.
- **Classical memory:** W = Σ_j ρ_j^{A_I} ⊗ T_j^{A_O B_I} ⊗ … — a **separable** (in the
  temporal cut) mixture; the environment is a classical feedback register that *measures* the
  system each step and conditions later evolution on the outcome j.
- **Quantum memory:** anything that is **not** of the separable form above ⇒ the process matrix
  is **entangled** across the A_I | A_O B_I partition. Quantum memory ⟺ temporal entanglement.
Detecting quantum memory therefore reduces to **entanglement detection on W**: a witness Z with
Tr(Z W_Cl) ≥ 0 for all classical-memory W, and Tr(Z W) < 0 flagging quantum memory; found by an
SDP over the separable-set relaxations (PPT, then DPS/Doherty extensions). Measuring ⟨Z⟩
requires only performing the local CP maps at each station — not full process tomography — but
it does require *performing local operations* (active interventions).

## Key equations / criteria [paper]
Generalized Born rule (outcome probabilities through the process matrix):
> p(ℳ^A, ℳ^B, ⋯ | 𝒥^A, 𝒥^B, ⋯) = Tr[ W^{A_I A_O B_I B_O ⋯} ( M^{A_I A_O} ⊗ M^{B_I B_O} ⊗ ⋯ ) ]

where the M^{X_I X_O} are the **Choi matrices of the local operations** (CP maps / instrument
elements) the experimenter applies at each station.

**Markovian process** (verbatim mechanism): *"a Markovian process can be written as a tensor
product of the initial state and the Choi matrices of the different channels that connect the
measurement stations."*
> W_M^{AB⋯} = ρ^{A_I} ⊗ T^{A_O B_I} ⊗ ⋯

**Classical-memory process** (verbatim mechanism): *"A non-Markovian process with classical
memory is one where, during each system-environment interaction, the environment obtains some
classical information about the system, which can affect future such interactions."* … *"the
environment can be simulated as a feedback mechanism, which measures the system at each time
step and, conditioned on the outcome, affects the system's evolution at future times."*
> W_Cl^{AB⋯} = Σ_j ρ_j^{A_I} ⊗ T_j^{A_O B_I} ⊗ ⋯   (each term PSD)

Mathematical signature (verbatim): *"a process matrix with classical memory is proportional to
a separable state."* Hence:
> **Quantum memory ⟺ W is ENTANGLED across the cut A_I | A_O B_I** (i.e. not of the separable
> form above). Verbatim: *"Quantum memory corresponds to entanglement between A and B, which is
> A_I and A_O B_I"* ; *"detecting entanglement of the state translates to detecting a quantum
> memory for the process."*

**Quantum-memory witness** (verbatim): *"a hermitian operator Z whose expectation value is
positive for all process matrices with classical memory: ⟨Z⟩ = Tr(Z W_Cl) ≥ 0."* Operational
two-step form: Z = Σ_{i,j} α_{i,j} M_i^{A_I A_O} ⊗ M_j^{B_I}. A value Tr(Z W) < 0 certifies
quantum memory.

**SDP (find the witness / test separability of W):** first level = PPT relaxation
> minimize Tr(Z ρ^{T_A}) s.t. Z Hermitian PSD, Tr(Z)=1
second level = **Doherty–Parrilo–Spedalieri (DPS) / symmetric extension** hierarchy: apply PPT
to the extended state ρ̃^{ABA} with ρ̃ ≥ 0, ρ̃^{T_A} ≥ 0, ρ̃^{T_B} ≥ 0.

**Multi-time (n ≥ 2 steps):** classical memory generalizes to
> W_Cl^{A¹⋯A^n} = Σ_x ρ_x^{A¹_I} ⊗ T_x^{A¹_O A²_I} ⊗ ⋯ ⊗ T_x^{A^{n-1}_O A^n_I}   (each term PSD)
with the separability / witness criterion applied to the multipartite temporal partition
A¹_I | A¹_O A²_I | ⋯ | A^{n-1}_O A^n_I. The framework is dimension-general (any finite d).

## Relevance to project [ours]
**(A) Certifies "revival ≠ quantum" at the right level [paper→ours].** This is the multi-time
statement of exactly what broke our bare-backflow witness. A classical-memory process
(feedback register that measures-and-reprepares) is *separable* in the temporal cut and passes
the witness (⟨Z⟩ ≥ 0). Classical non-Markovian noise — including our RTN forgery — is a
classical feedback mechanism, so it lives in W_Cl and CANNOT make Tr(Z W) < 0. The witness fires
**only** on temporal entanglement of the process. This is the process-tensor analogue of
Bäcker's E#[χ1] < E[χ2] assistance criterion and independently confirms: non-Markovianity
(memory) ⊋ quantum memory; only the entanglement/assistance-exceeding-bound part is genuinely
quantum. [ours] So this paper is a valid, literature-grade tool for the "genuine quantum memory"
claim.

**(B) FLAG-#1 VERDICT — it needs ACTIVE interventions, NOT a passive record [paper→ours,
decisive].** The witness is a functional of the process matrix W, and W is defined operationally
through **local operations the experimenter performs** at each station: *"an experimenter can
intervene on the system, e.g. by measuring or transforming it. Each operation can be
represented by a completely positive map."* Measuring ⟨Z⟩ *"only requires performing the CP maps
… and does not require full process tomography"* — i.e. it saves you from reconstructing all of
W, but it **still requires you to APPLY the CP maps** (informationally structured instruments)
at each time and feed the output A_O forward into the next station's input B_I. That output-wire
feed-forward is the crux: a **passive syndrome record** gives you outcomes under a *fixed,
non-interventional* readout — there is no A_O output wire being re-prepared and propagated, so
the object you can build from a passive record is a *classical multi-time outcome distribution*,
not the process matrix W. **The Giarmatzi–Costa witness does NOT resolve Flag #1 in the passive
direction:** it certifies quantum memory expressed in the ACTIVE single-/multi-time
interventional process object, not quantum memory expressed on the passive syndrome record. If
our simulator's genuine quantum memory is only certifiable via this witness, it lives in the
interventional object and would require active control to expose — consistent with our standing
worry that quantum memory may be *twirled out* of the passive record. This is a **STOP-consistent
finding for Flag #1**, not a resolution. [ours]

**(C) What WOULD be needed for the passive case [ours].** To certify quantum memory on a passive
record we need a witness whose inputs are outcome sequences under a *fixed* measurement (no
output-wire feed-forward). Giarmatzi–Costa does not provide that; it is the correct tool only if
we are allowed to insert instruments (e.g. active tomographic control pulses between syndrome
rounds). Any claim that the passive syndrome record carries *quantum* memory must be argued by a
different instrument (or by showing the passive record's multi-time statistics cannot be
reproduced by any W_Cl — a strictly harder, and here unaddressed, question).

**(D) d>2 / multi-qubit / multi-time [paper].** Dimension-general (finite d, so d>2 and
multi-qubit are covered) and defined for arbitrary n time steps via the multipartite temporal
partition above. So the *scaling* is not the obstacle; the obstacle is the **active-instrument**
data requirement.

## Decisive verbatim quotes [paper]
- Born rule: *"p(ℳ^A, ℳ^B, ⋯ | 𝒥^A, 𝒥^B, ⋯) = Tr[W^{A_I A_O B_I B_O ⋯} (M^{A_I A_O} ⊗ M^{B_I B_O} ⊗ ⋯)]."*
- Markov: *"a Markovian process can be written as a tensor product of the initial state and the
  Choi matrices of the different channels that connect the measurement stations."*
- Classical memory (mechanism): *"the environment can be simulated as a feedback mechanism, which
  measures the system at each time step and, conditioned on the outcome, affects the system's
  evolution at future times."*
- Classical memory (signature): *"a process matrix with classical memory is proportional to a
  separable state."*
- Quantum memory: *"Quantum memory corresponds to entanglement between A and B, which is A_I and
  A_O B_I"* ; *"detecting entanglement of the state translates to detecting a quantum memory for
  the process."*
- Witness: *"a quantum memory witness is a hermitian operator Z whose expectation value is
  positive for all process matrices with classical memory: ⟨Z⟩ = Tr(Z W_Cl) ≥ 0."*
- **Operational (Flag-#1 decisive):** *"Each time step can be seen as a 'measurement station',
  labelled A, B, …, where an experimenter can intervene on the system, e.g. by measuring or
  transforming it. Each operation can be represented by a completely positive map."*
- **Operational (Flag-#1 decisive):** *"Crucially, measuring the witness only requires performing
  the CP maps [at each station] and does not require full process tomography."*
