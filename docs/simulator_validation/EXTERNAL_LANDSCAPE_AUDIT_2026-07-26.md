# External landscape audit — what is already solved elsewhere, and what is not

Date: 2026-07-26. Scope: the implementations retained under `external/`, read against this
repository's stated deliverable.

This is a **positioning** record, not a scientific claim. It changes no carrier status and licenses
no new language. It exists because three capabilities this repository was treating as its frontier
turned out to be published work or a thin adaptor over an installed dependency, and that fact must
be written down where the next reader will find it before spending a month rebuilding them.

## What was surveyed

`external/`: `deltakit` (Riverlane QEC stack, 86.6k LOC), `yaqs` (54.4k), `mitiq` (40.0k),
`OQuPy` (19.6k), `ACE`; `external/baselines/`: `Stim`, `qecsim` (24.2k), `ITensorMPS.jl` (20.0k),
`qiskit-aer`, `corrqec`, `PyMatching`, `BeliefMatching`, `fusion-blossom`, `qecGPT`, `DMLE-QEC`;
`external/reference_repos/`: `tn_qsim` (14.0k), `OpenQMC-simulator`.

## Already solved outside this repository

**Distance-parameterised code, schedule, detector fold, and observable.**
`stim.Circuit.generated("surface_code:rotated_memory_z", distance=d, rounds=r, <4 noise knobs>)`
emits the complete experiment at any distance. Verified live: d3 26 qubits / 24 detectors,
d5 64 / 120, d7 118 / 336, 20k shots instant. Apache-2.0, and already a pinned direct dependency at
`stim==1.16.0` (`core-environment-cu130.lock:10`).

`stim.Circuit.shortest_graphlike_error()` returns 3, 5, 7 for d = 3, 5, 7 — a one-line executable
falsifier that a circuit claimed to be distance d actually has distance d. This repository has no
equivalent check on its own constructors.

**The 2D PEPO/PEPDO surface code under exact amplitude damping and exact coherent rotation.**
Darmawan & Poulin, PRL 119, 040502 (2017) (arXiv:1607.06460), reimplemented at 3×3 and 5×5 in
`external/reference_repos/tn_qsim/surface.py:132-168`. Their carrier is a manifestly-PSD locally
purified PEPDO (`pepdo.py:18,110-123`), better conditioned than this repository's density-matrix
PEPO. Code-capacity single-shot only.

**Untwirled non-Pauli qutrit leakage on a quasi-1D code at several hundred qudits.**
Manabe, Suzuki & Darmawan, *Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes
Using Tensor Network Methods*, **arXiv:2308.08186v2** (21 Jan 2025), read directly from the retained
PDF (sha256 `be54fe2e…`, 15 pp). MPS ansatz, canonical update with SVD truncation to bond dimension
χ, Kraus operators sampled per trajectory (Eq. A9). Exact coherent leakage, noisy CZ with a leaked-control
phase, leakage spreading, thermal Lindblad idling, and a leaked-readout CP-instrument — no twirl.

**The scale figure must not be attributed to a surface code.** d = 99 over 99 rounds on ~197 qutrits
is the **1D repetition code** (2d − 1 qubits; Fig. 5 and Fig. 11 captions). Their surface code is the
**thin 3 × d** patch — 6d − 1 qubits, width fixed at 3 — and the paper states that "for the d ≥ 5
simulation, the cost of performing SVD becomes a crucial bottleneck" on their single CPU node. For
the thin code, d is the **Z-distance**: the X logical operator has fixed length, so the logical X
error rate *increases* with d.

**They emit a logical error rate, not a Record.** The word "detector" occurs **zero times** in the
paper; syndromes are decoded by minimum-weight perfect matching and "the probability of decoding
failure" is the reported quantity. There is no temporal fold to compare with ours.

**The paper leaves d × d open and names the tool.** "Extending these methods to codes with more
complex connectivity in two or higher dimensions will likely require tensor network ansatz beyond
MPS, which we leave to future work", because a 1D ansatz snaked through a 2D lattice has a cost that
"will typically grow exponentially with increasing the second dimension". It also records that
state-vector simulation needs "a few petabytes of memory for 30 qutrit systems" — so this
repository's 3^25 wall at d5 is real and fundamental to the state-vector approach, and the
`sv_traj_d3_wc` nine-qutrit kernel specialisation is a separate, removable artefact sitting on top
of a genuine wall.

Read status: **incomplete** by the `deep-read-paper` gate — no PDF renderer is available in this
environment, so the load-bearing equations (1)–(10) were text-extracted but not visually verified,
and no independent source-only review has been done. The structural findings above are prose-level
and corroborated across the abstract, Sec. III, Sec. IV, the figure captions and the conclusion; the
equation transcriptions are not yet admissible evidence. Two duplicate notes for this source exist
(`leakage_tensor_network_simulation_2308.08186.md`, `manabe_suzuki_darmawan_leakage_tn_2308.08186.md`),
both failing the audit for missing front matter; `literature_schema` keys on `source_id`, so one must
be retired before either can be admitted.

**That a Pauli twirl loses structure this repository cares about.** Already measured and published:
the generalized twirling approximation over-predicts the logical error rate by more than 3×
(`tn_qsim/repetition_code_simulation_with_GTA.py:127-140`). The premise is externally supported,
which also means it is not this repository's to establish.

**A real-code multi-round Record under a genuine Kraus (non-Pauli) channel.** Reported from a
prototype built this session over `qiskit-aer` 0.17.2 `matrix_product_state` in the existing
`ecs-baseline-aer` environment, driven from a stim-generated rotated surface code: d3 26 qubits /
3 rounds / 24 detectors at 1.7 ms/shot, d5 64 / 5 / 120 at 18.3 s/shot, with the Kraus and
exactly-twirled detector-fire rates differing by 16.9σ at d3. Aer's `density_matrix` method refuses
d3 at 262 GB, so a trajectory carrier is the only route at patch scale.

**Verification status of the preceding paragraph:** the stim→JSON translation step was reproduced
independently (d3 26 qubits / 24 detectors / 33 measurements; d5 64 / 120 / 145). The Aer timings
and the 16.9σ separation are **agent-reported and not independently reproduced** — the re-run
exceeded its time budget on the d5 leg. Treat both numbers as indicative until a committed leg
reproduces them.

## What remains unoccupied

Four things, and the list is deliberately short.

**1. Local dimension > 2 inside a real d×d patch Record — NARROWED 2026-07-26, see below.**
`qiskit-aer` is qubit-only and cannot represent leakage at all. `qecsim` is Pauli-only. Manabe et al.
carry qutrits but hold the patch width fixed at 3, and say why: a 1D MPS snaked through a 2D lattice
costs exponentially in the second dimension, so they explicitly defer two-dimensional connectivity
to "tensor network ansatz beyond MPS".

**Refuted at d3 by external search.** Varbanov, Battistel, Tarasinski, Ostroukh, O'Brien, DiCarlo &
Terhal, arXiv:2002.07119v1 (2020), retained at `docs/papers/2002.07119v1.pdf`, run density-matrix
simulations of the distance-3 Surface-17 patch in which the leakage-prone qubits "are included as
three-level systems" with ancilla measurement "modeled as projective in the {|0>,|1>,|2>} basis"
(:292-296), over multiple QEC cycles, and report defect probabilities per stabilizer. Local
dimension > 2 inside a real d3 patch with multi-round syndrome data is therefore **occupied**.

What may remain, and is untested: scale beyond a density matrix, and the Record-as-emitted-artifact
framing rather than defect probabilities computed inside the analysis. Neither has been checked
against the literature. Do not restate this row as a differentiator without doing so.

**2. A replayable, time-correlated source process driving noise parameters across gates and
rounds.** `qiskit-aer`'s `NoiseModel` is IID per gate instance and structurally cannot express a
correlated timeline. `tn_qsim` draws its coherent rotation once per shot — the quasi-static
degenerate case. `OQuPy` and `OpenQMC` carry continuous-time correlation but have no measurement
primitive. Owned here by `source/` and its explicit source-to-parameter mapping.

**3. The Record as a first-class emitted, schema-versioned, provenance-bound artifact with
fail-closed truncation.** None of the surveyed implementations emits a Record at all: `tn_qsim`
retains four scalars and discards the record, `qecsim` discards the `(time_steps, n_stab)` syndrome
inside `_run_once`, and `ITensorMPS`'s MPDO Frobenius-SVD truncation can yield negative or complex
measurement probabilities with only a printed warning (`src/mpo.jl:1074`). The `BondAbortError`
discipline, the representability policy, and the versioned artifact schemas have no counterpart
here.

**4. The evaluator/certify boundary.** An isolated hand-typed operator reference the production
builders must match before execution is authorized, plus corrupt-stabilizer and record-shuffle
negative controls behind one fail-closed verdict. `tn_qsim` has no tests over its QEC drivers;
`qecsim`'s tensor code is a decoder, not a carrier.

## What this changes

"Produce a multi-round Record for a real surface-code patch under a declared non-Pauli noise
process" is no longer a distinguishing deliverable. Any scope statement, roadmap, or completion
language that rests on it should be rewritten against the four items above instead.

Items 3 and 4 are worth naming explicitly, because they are the parts of this repository's
discipline most often read as overhead. They are, on this survey, the two capabilities with no
external counterpart at all.

## Five reference clones read, 2026-07-26

Cloned to test whether precedent exists in code that no paper describes:
`qutrits` at `fe24c42`, `restless-simulator` at `92e8a62`, `surface-code-simulator` at `f06123e`,
`Located-decoder-for-Rydberg-decay` at `1bf10b6`, and `quantumsim` (default `292fce9`, plus its
other remote refs).

**Zero of five apply a deterministic single-qubit layer inside a cycle while carrying a leaked
level.** The strongest candidate was checked exhaustively rather than at its default:
`git grep -i -E "dynamical|decoupl|refocus|pauli_frame|pauli frame"` over every `*.py` on all 34 of
quantumsim's remote refs returns zero hits on every ref. The other four cannot host the question —
`qutrits` rejects measurement outright, `restless-simulator` has shots not rounds,
`Located-decoder-for-Rydberg-decay` contains no circuit or quantum state, and
`surface-code-simulator` is a typed wrapper over `stim.Circuit.generated`.

**Zero of five do circuit-level frame bookkeeping.** What the reads surfaced is three different
objects that must not be conflated with it: compile-time support tracking (quantumsim's surviving
basis labels), classical readout post-processing (restless XOR differencing, lag-1 over shots of
independent calibration circuits, not lag-2 over rounds), and decoder-side herald annotation
(`Located-decoder`'s `fault_ids` plus weight-0 erasure edges). No leakage indicator bit exists
anywhere in the five.

Five more repositories of silence still do not establish a field-wide gap.

### The finding that matters: the leaked-inert assumption is underdetermined

quantumsim ships `R_y(pi) = (-iY) (+) 1`, not `Y (+) 1`. The conjugation identity is unaffected —
the extra phase is diagonal, so both conventions give `U^dag Z U = diag(-1,+1,+1) = -Z + 2|2><2|`,
and quantumsim therefore corroborates the identity our stabilizer-sign argument rests on. What
diverges is `Y^2 = I`: under their convention two pi pulses flip the sign of a `|0><2|` coherence,
so it fails as a channel.

The consequence is about the literature, not the code. "Single-qubit gates act on a leaked state as
the identity" fixes the `|2><2|` entry to modulus 1 but leaves its **phase relative to the
computational block free**. Two implementations that both satisfy the sentence verbatim are
physically inequivalent the moment `|2>`-computational coherence exists — and the CZ `|11> <-> |02>`
exchange generates exactly that coherence. This is not a code-versus-paper contradiction; the
assumption is simply underdetermined. Any preregistration resting on it must state the phase
convention explicitly and cannot use the Varbanov sentence to fix it.

### Adoptable, if wanted

- `restless-simulator`'s `QutritUnitaryGate.from_qubit_gate`
  (`restless_simulator/circuit/qutrit_unitary_gate.py:127-193` at `92e8a62`), Apache-2.0 (IBM 2023).
  Seeds `np.eye(3**n)` and overwrites only computational entries, so identity-on-`|2>` is automatic.
  Useful as an independent third-party cross-check on our qutrit embedding, not as a dependency. Its
  `test_two_qutrit_gate` pins RZZ to identity on *every* leaked basis state — stronger than anything
  Varbanov asserts, and wrong for our explicit CZ transport, so it doubles as a ready-made falsifier
  of a divergence we would have to make deliberately.
- quantumsim's `optimize` / `optimal_bases` (`quantumsim/circuits/compiler.py:9-42, 345-406`). An
  SVD-derived per-qubit subbasis whose reduction is derived from the operator rather than declared
  by the caller, and whose surviving label set is itself a standing falsifier.

## Excluded on evidence

- `yaqs` rejects `reset` and mid-circuit measurement outright (`dag_utils.py:49`,
  `digital_tjm.py:135-143`), so it cannot express a syndrome-extraction round.
- `OQuPy` and `ACE` have no circuit, register, measurement, or shot concept; their output is
  Tr[O ρ(t)].
- `mitiq` is error mitigation only, and is GPLv3.
- `OpenQMC-simulator` has no license file and no measurement primitive.
