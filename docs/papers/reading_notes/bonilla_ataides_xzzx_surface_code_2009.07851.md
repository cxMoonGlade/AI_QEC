# Full-text review — Bonilla Ataides et al., "The XZZX surface code" (arXiv:2009.07851v3)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** The pinned final-author PDF
> `2009.07851v3` was acquired temporarily with
> `.agents/skills/deep-read-paper/scripts/fetch_and_extract.py`; no PDF was added to the
> repository because this task authorized only the reading note. At audit time the temporary
> paths were `/tmp/deep-read-paper.44gusu1z/2009.07851v3.pdf`, `.txt`, and
> `.provenance.json`. The PDF was 734,368 bytes, 16 pages, SHA-256
> `4b4f244f949b0d1e862ff44e6328f33abab93654cd64a7e5f1ada0467ccaafd7`; extraction used
> PyMuPDF only for navigation. The PDF signature, page count, metadata, head, tail, and arXiv
> submission history were checked. Reacquire the same object from
> `https://arxiv.org/pdf/2009.07851v3` and verify the hash before reusing exact locators.
>
> **Visual verification.** PDF pp. 2, 3, 4, 6, 9, and 12 were rendered at 180 dpi and
> inspected directly: Fig. 1 (XZZX stabilizers and boundaries), Eq. (1), Fig. 3 and its
> threshold caveat, Fig. 5 and the phenomenological ancilla paragraph, Fig. 7 (logical-patch
> initialization, not syndrome-ancilla reset), and Eqs. (5)-(6). Text extraction was not used
> as formula ground truth.

## Metadata [paper]

- **Authors:** J. Pablo Bonilla Ataides, David K. Tuckett, Stephen D. Bartlett, Steven T.
  Flammia, and Benjamin J. Brown.
- **Affiliations:** Centre for Engineered Quantum Systems, University of Sydney; AWS Center
  for Quantum Computing.
- **Journal:** *Nature Communications* **12**, article 2172 (2021), published 12 April 2021.
- **DOI:** `10.1038/s41467-021-22274-1`.
- **Version read:** arXiv `2009.07851v3`, revised 19 April 2021 and labelled by the authors as
  the final-author version. The journal DOI and arXiv version history were verified from their
  primary metadata pages.
- **Type:** theory plus classical Monte Carlo/tensor-network decoding simulation; not a
  hardware experiment and not a quantum-channel leakage simulation.
- **Ancillary material:** the paper links public data/code at
  `https://bitbucket.org/qecsim/qsdxzzx/`. The versioned PDF contains the main article,
  Methods, and references. No separate scientific supplement is identified on the publisher
  page; its separately listed PDF is the peer-review file.

## Executive summary [paper]

The paper defines and benchmarks a non-CSS surface-code variant whose bulk face stabilizer is
the product `XZZX`. A Hadamard change of basis on alternating qubits makes it locally equivalent
to the conventional surface code, while aligning dominant `Z`-error strings along independent
diagonals. Under independent single-qubit Pauli noise, approximate maximum-likelihood decoding
gives a minimum code-capacity threshold of `18.7(1)%` at depolarizing noise and thresholds near
`50%` at the pure-Pauli corners (PDF p. 4, Fig. 3 discussion). Under a phenomenological model
with unreliable stabilizer outcomes, repeated measurements and an anisotropic MWPM decoder give
a threshold approaching `~10%` at infinite bias (PDF p. 6, Fig. 5).

## Selection + coverage [ours]

This source is load-bearing for the **XZZX code and phenomenological syndrome component**, not
for a qutrit leakage carrier. The assigned rows are deliberately split:

| assigned row | role of this source |
|---|---|
| explicit XZZX stabilizer geometry | primary source |
| repeated noisy stabilizer outcomes and detector construction | primary phenomenological source |
| explicit ancilla measurement circuit | only a leading-order verbal sketch, not the simulated object |
| syndrome-ancilla reinitialization/reset | not supplied |
| transmon-qutrit leakage dynamics | not supplied |
| quarter-touch channel `exp(L/4)` | not supplied |
| full joint multi-round syndrome/observable record law | not supplied |

No contrary source was assigned. The companion Darmawan et al. Kerr-cat paper
(`arXiv:2104.09539v2`) was read separately: it supplies a more explicit circuit, but its bosonic
Kerr-cat noise object is not the transmon-qutrit leakage object either.

## Notation + source-location ledger [paper]

| symbol | domain / status | definition and assumptions | exact location |
|---|---|---|---|
| `S_f` | fixed Pauli stabilizer for face `f` | bulk face has two `X` and two `Z` factors; codespace is the common `+1` eigenspace | PDF p. 2, Fig. 1(a) and caption |
| `E` | sampled Pauli error, `E in P` | a defect occurs at `f` when `S_f E = -E S_f` | PDF p. 3, left column |
| `d`, `n`, `k` | code parameters | `n=O(d^2)` physical qubits and `k=O(1)` logical qubits; constants depend on boundaries | PDF p. 2, Results |
| `d_X`, `d_Z` | positive integer distances | minimum weights of all-`X` and all-`Z` logical operators for rectangular layout | PDF pp. 2 and 8, Fig. 1(h), Eq. (4) context |
| `E(rho)` | single-qubit CPTP Pauli channel | `(1-p)rho + p(r_X XrhoX + r_Y YrhoY + r_Z ZrhoZ)` with nonnegative `r` summing to one | PDF p. 3, Eq. (1), visually checked |
| `eta` | nonnegative bias parameter | for `Z` bias, `eta=r_Z/(r_X+r_Y)` with `r_X=r_Y`; `eta=1/2` is depolarizing and `eta -> infinity` is pure `Z` | PDF p. 4, below Fig. 3 |
| `p_h.r.`, `p_l.r.` | per-time-step error probabilities | high-rate `Z` error versus each low-rate `X`/`Y` error | PDF pp. 5-6, fault-tolerant-threshold model |
| `q` | measurement-outcome flip probability | `q=p_h.r.+p_l.r.` in the phenomenological model | PDF p. 6, lower-left paragraph |
| `t`, `Delta` | discrete round index / one-round interval | stabilizers are measured at black spacetime vertices; a changed outcome is a defect | PDF p. 6, Fig. 5(a-d) |
| `u,v` | defect vertices | MWPM pairs defects using the most likely connecting string `E_{u,v}` | PDF pp. 11-12, Methods |
| `l_x'`, `l_y'`, `l_t` | nonnegative integer separations | distances along the two code-aligned spatial axes and time | PDF p. 12, Eqs. (5)-(6), visually checked |
| `p_c` | asymptotic threshold estimate | crossing/critical-exponent estimate, not a per-cycle record metric | PDF pp. 3-6 and Methods pp. 11-13 |

`P` is overloaded: `mathcal P` denotes the Pauli group near PDF p. 3, while `P` later denotes
logical failure probability in the overhead analysis (PDF pp. 7-8). Neither is a full joint
syndrome-record distribution.

## Method (deep) [paper]

### Code and code-capacity model

The local Hadamard-equivalent XZZX layout is specified by Fig. 1. For code-capacity studies the
physical model is exactly the memoryless single-qubit Pauli channel in Eq. (1). A tensor-network
approximation to maximum-likelihood decoding contracts logical-coset probabilities, retaining
the largest `chi` Schmidt values; `chi=16` is used broadly, while the high-bias large-distance
study uses `chi=8` after convergence checks (Methods, PDF p. 11, Fig. 8).

### Phenomenological repeated-measurement model

The fault-tolerant study applies independent high-rate `Z` errors, low-rate `X/Y` errors, and an
independent incorrect stabilizer outcome with probability `q`. It repeats stabilizer measurements
and defines spacetime defects by outcome changes. Fig. 5 shows data errors as spatial strings and
measurement errors as temporal strings. The anisotropic MWPM edge score is

```text
-log prob(E_uv) proportional to l_x' w_h.r. + l_y' w_l.r. + l_t w_t,
w_t = -log(q/(1-q)).
```

This is Eq. (6), PDF p. 12. It is a decoder weight for an explicitly uncorrelated
phenomenological model, not a generator-to-channel derivation.

### What the paper says about an ancilla circuit

The lower-left paragraph on PDF p. 6 says, explicitly only **to leading order**, that its scalar
measurement-flip rate is consistent with preparing an ancilla in `|+>`, entangling it to the
four data qubits with bias-preserving controlled-not and controlled-phase gates, then measuring
the ancilla in the `X` basis. The actual threshold simulation remains the phenomenological
outcome-flip model. No gate order, Kraus instrument, post-measurement state, or ancilla reset map
is specified there.

PDF p. 9, Fig. 7 concerns initialization/readout of **logical surface-code patches** for lattice
surgery. It is not evidence for syndrome-ancilla reinitialization between extraction rounds.

## The MECHANISM [paper]

The load-bearing mechanism in this paper is independent biased **Pauli** noise plus independent
phenomenological measurement flips. In the infinite-`Z`-bias limit, diagonal stabilizer products
commute with the noise, imposing parity conservation and reducing decoding to disjoint repetition
codes (PDF pp. 2-3, Fig. 1(d-e)). Finite-bias low-rate errors couple those diagonals.

The paper does not propagate a bosonic, transmon, qutrit, Lindblad, or leakage state. It therefore
does not establish any amplitude or coherent population transfer involving `|2>`, nor a seepage,
heating, or reset channel.

## Mechanism mapping to error_coupling_simulator [ours]

- The reusable part is the **code geometry**: an XZZX face check and its spatial/temporal defect
  semantics.
- The paper's scalar phenomenological measurement flip can at most serve as a reduced regression
  target. It is not an implementation recipe for a physical ancilla instrument.
- Mapping a project transmon-qutrit Liouvillian to these Pauli/outcome-flip probabilities requires
  an additional independently derived reduction. The paper never performs that bridge.
- The occurrence of factors `d/4` in the paper's low-rate logical-string counting (Eqs. (3),
  (7)-(9)) is unrelated to a per-touch channel `exp(L/4)`. Treating it as support for that channel
  slicing would be a category error.

## The OBSERVABLE / metric [paper]

The primary observables are logical failure probability and its asymptotic threshold `p_c` under
a specified decoder. For the repeated-measurement model, the decoder consumes a set of spacetime
defects created by differences of consecutive stabilizer outcomes. The paper samples enough
histories to estimate LER/threshold, but it does not define or report the full joint law
`P(s_1,...,s_R,m)`, record TV/KL/NLL, or a retained shot-level record artifact.

The paper also warns, implicitly through method choice, that its suboptimal matching decoder does
not use all syndrome information (PDF p. 5). Its threshold is therefore not an information-complete
observable of the underlying process.

## Findings + numbers [paper]

| result | value | exact location |
|---|---:|---|
| XZZX code-capacity threshold at depolarizing noise | `18.7(1)%` | PDF p. 4, text below Fig. 3 |
| pure `X`, `Y`, or `Z` corners | approximately `50%` | PDF p. 4, same paragraph |
| largest-distance excess above hashing bound at `eta=30,100,1000` | `1.2(2)%`, `1.6(3)%`, `3.7(3)%` | PDF p. 5 |
| phenomenological high-bias threshold | tends to approximately `10%` | PDF p. 6, Fig. 5(e) and text |
| ideal pure-`Z` repetition-code limit | `50%` | PDF p. 3 |

The above are numerical estimates within the paper's Pauli/phenomenological models. They are not
hardware leakage parameters and should not be copied into a qutrit noise fixture.

## Limitations [paper]

- The code-capacity model is independent single-qubit Pauli noise.
- The fault-tolerant model is phenomenological; the ancilla circuit is invoked only as a
  leading-order consistency motivation for `q`.
- The authors leave detailed fault-tolerant-computation implementation and threshold questions
  around their lattice-surgery sketch to future work (PDF p. 9).
- Circuit-level noise and correlated-error generalizations are explicitly future directions
  (Discussion, PDF p. 10).
- Approximate TN and MWPM decoders are used; matching omits some syndrome information.
- No leakage Hilbert space, physical reset channel, multitime channel/instrument, or full-record
  distribution is modeled.

## Contrary evidence and failure regimes [paper]

- Apparent threshold excess over the zero-rate hashing bound is presented as numerical evidence
  that warrants further study, not as a theorem (PDF pp. 4-5).
- The nominal `~10.3%` high-bias phenomenological limit is slightly undershot; the authors attribute
  this to finite-size effects (PDF p. 6).
- Finite-bias `X/Y` errors break the independent diagonal repetition-code structure.
- Fig. 7's logical-patch initialization must not be misread as a syndrome-ancilla reset primitive.

## Project kill conditions [ours]

This source cannot be used to authorize a project claim if that claim requires any of the
following: a transmon-qutrit leakage mechanism, a calibrated physical leakage value, a uniform
quarter-touch exponentiation, a CPTP ancilla reset instrument, or a full-joint record oracle.
Any derivation that cites this paper for one of those rows fails closed. It remains valid support
for the XZZX stabilizer and phenomenological detector geometry only.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| square lattice with data qubits on vertices | assign the same two-`X`, two-`Z` face check | local Hadamard equivalence to surface code | XZZX stabilizer code | PDF p. 2, Fig. 1(a-b) | `matched` |
| independent Pauli error | anticommute test `S_f E=-E S_f` | perfect code-capacity measurement | spatial defect set | PDF p. 3 | `matched` |
| per-round data errors plus scalar outcome flips | compare consecutive check outcomes | independent phenomenological noise; `q=p_h.r.+p_l.r.` | 2+1D spacetime defects | PDF pp. 5-6, Fig. 5 | `matched` |
| defect vertices `u,v` | anisotropic negative-log edge weight | most likely connecting string; uncorrelated noise | MWPM correction | PDF p. 12, Eqs. (5)-(6) | `matched` |
| ancilla `ket(+)` and four data qubits | bias-preserving controlled gates then `X` measurement | asserted only to leading order | motivation for scalar `q` | PDF p. 6, lower-left paragraph | `matched` only as a sketch |
| measured ancilla | reinitialize/reset for next extraction round | no map or schedule supplied | fixed next-round ancilla state | nowhere in full text | `unsupported` |
| transmon-qutrit state and Liouvillian `L` | evolve each of four touches by `exp(L/4)` | no such Hilbert space or normalization | qutrit leakage trajectory | nowhere in full text | `unsupported` |
| all round outcomes and logical bit | retain/score complete joint probability | paper aggregates through decoder | full joint record distribution | nowhere in full text | `unsupported` |

Because the last three rows are unsupported, this paper cannot close the project's physical
qutrit-instrument bridge.

## Relevance to error_coupling_simulator [ours]

Reuse the XZZX face orientation, boundary semantics, and consecutive-outcome detector definition.
Do not reuse the phenomenological scalar `q` as though it were derived from the project's physical
carrier. Most importantly, this reading corrects a possible overreach: a canonical XZZX source is
not automatically a source for the project's leakage generator, channel normalization, reset
instrument, or full-record oracle.

## How to use / trust + open questions [ours]

**Trust level:** complete full-text read of a pinned final-author version; load-bearing figures and
equations visually checked. The temporary artifacts were intentionally not persisted, so future
load-bearing reuse should reacquire `v3` and verify the recorded SHA-256.

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| XZZX bulk stabilizer | PDF p. 2, Fig. 1(a) | every bulk face has the same two-`X`, two-`Z` check | no qutrit realization | `closed` |
| repeated noisy syndrome / detector geometry | PDF p. 6, Fig. 5; p. 12 Eq. (6) | changed outcomes form spacetime defects for MWPM | no full record distribution | `closed` |
| leading-order ancilla measurement sketch | PDF p. 6, lower-left | `ket(+)` ancilla, controlled gates, `X` measurement can motivate `q` | no simulated physical circuit/instrument | `closed` only for the sketch |
| syndrome-ancilla reinitialization | full text; p. 9 Fig. 7 checked as a different object | nothing | no post-measurement reset/reprepare map | `missing` |
| transmon-qutrit leakage carrier | full text | nothing | no `ket(2)` population/coherence or qutrit channel | `missing` |
| `exp(L/4)` quarter-touch normalization | full text; `d/4` occurrences checked and unrelated | nothing | no Liouvillian channel slicing | `missing` |
| full joint multi-round record law/oracle | full text | histories feed a decoder and threshold estimate | no `P(record)`, TV/KL/NLL, or shot artifact | `missing` |

**`read_status: complete`**

**`evidence_status: persisted`**
