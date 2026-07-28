# Full-text review — Darmawan et al., "Practical quantum error correction with the XZZX code and Kerr-cat qubits" (arXiv:2104.09539v2)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** The pinned PDF
> `2104.09539v2` was acquired temporarily with
> `.agents/skills/deep-read-paper/scripts/fetch_and_extract.py`; no PDF was added to the
> repository because this task authorized only the reading note. At audit time the temporary
> paths were `/tmp/deep-read-paper.44gusu1z/2104.09539v2.pdf`, `.txt`, and
> `.provenance.json`. The PDF was 6,679,581 bytes, 21 pages, SHA-256
> `809149344e94392151a3935a4ec9615930e19d7aee414a9d022a7ac07036e5e5`; extraction used
> PyMuPDF only for navigation. The PDF signature, page count, metadata, head, tail, and arXiv
> submission history were checked. Reacquire the same object from
> `https://arxiv.org/pdf/2104.09539v2` and verify the hash before reusing exact locators.
>
> **Visual verification.** PDF pp. 3, 4, 6, 7, 10, 11, 12, and 17 were rendered at 180 dpi
> and inspected directly: Fig. 2 (XZZX stabilizer plus ancilla parity circuit), Eq. (1) and
> Fig. 3 (Kerr-cat carrier), Eq. (2) (bias-preserving CX Hamiltonian), Figs. 5-6 and the
> post-measurement reinitialization paragraph, the explicit residual-leakage omission, Table II
> and Fig. 8, the round-time comparison, and Eq. (A1). Text extraction was not used as formula
> ground truth.

## Metadata [paper]

- **Authors:** Andrew S. Darmawan, Benjamin J. Brown, Arne L. Grimsmo, David K. Tuckett, and
  Shruti Puri.
- **Affiliations:** Yukawa Institute for Theoretical Physics/JST PRESTO; University of Sydney;
  Yale University/Yale Quantum Institute.
- **Journal:** *PRX Quantum* **2**, 030345 (2021), published 16 September 2021.
- **DOI:** `10.1103/PRXQuantum.2.030345`.
- **Version read:** arXiv `2104.09539v2`, revised 18 October 2021; the journal DOI and arXiv
  version history were verified from primary metadata.
- **Type:** theoretical architecture plus Lindblad/stochastic-master-equation component
  simulation, circuit-level Pauli Monte Carlo, and small-code exact density-matrix simulation;
  not a device experiment.
- **Appendices:** Appendix A gives the Pauli and exact-simulation methods; Appendix B compares
  Kerr-cat and dissipative-cat gate leakage/fidelity. No separate supplement was required to
  read the stated method.

## Executive summary [paper]

The paper co-designs the XZZX surface code with biased-noise Kerr-cat qubits. It explicitly gives
an XZZX stabilizer-extraction circuit, a bosonic Kerr-cat Hamiltonian and gate/readout operations,
and numerical channels derived from master-equation simulations. Large-code threshold simulations
then Pauli-twirl those channels and **discard residual leakage**. For a `6.25`-photon cat with
`n_th=8%` and two-photon dissipation `kappa_2=K/10`, the reported threshold is
`kappa/K ~ 2.5e-4`, corresponding to a bias-preserving-CX infidelity near `6.5%` and average CX
bias near `351` (PDF pp. 11-12, Table II/Fig. 8 and text).

## Selection + coverage [ours]

This source is load-bearing for an **explicit XZZX ancilla circuit and a concrete repeated-round
component model**. It is not direct evidence for the project's transmon-qutrit leakage carrier.

| assigned row | role of this source |
|---|---|
| explicit XZZX stabilizer and ancilla parity circuit | primary source |
| ancilla projective measurement and next-round reinitialization | primary Kerr-cat component source, with a fixed-state caveat |
| physical leakage mechanism | primary only for leakage out of a Kerr-cat subspace |
| propagation of residual leakage through full XZZX rounds | explicitly not done |
| transmon-qutrit leakage | different Hilbert space and mechanism |
| uniform `exp(L/4)` per touch | not supplied |
| full joint multi-round syndrome/observable record | not supplied |

No contrary source was assigned. Bonilla Ataides et al. (`arXiv:2009.07851v3`) was read as the
companion XZZX-code source; it supplies stabilizer/phenomenological-detector geometry but not this
paper's Kerr-cat circuit or any qutrit bridge.

## Notation + source-location ledger [paper]

| symbol | domain / status | definition and assumptions | exact location |
|---|---|---|---|
| `S_f` | face Pauli stabilizer | `X tensor Z tensor Z tensor X` on the four corners of a bulk face | PDF p. 3, Fig. 2(a) and text, visually checked |
| `S_f(t)` | measured sign at round `t` | a defect occurs when `S_f(t-1) S_f(t)=-1` | PDF p. 3, Sec. II.B |
| `A0`-`A4`, `D1`-`D4` | circuit error locations | ancilla locations and four data-gate locations in one check circuit | PDF p. 3, Fig. 2(b) |
| `a`, `a^dagger` | bosonic annihilation/creation operators | act on the SNAIL oscillator, not on a three-level transmon register | PDF p. 4, Eq. (1) |
| `K` | positive Kerr nonlinearity | sets nonlinear energy scale | PDF p. 4, Eq. (1) |
| `alpha` | coherent-state amplitude | cat size is approximately `abs(alpha)^2`; `ket(+/- alpha)` support logical states at large `alpha` | PDF pp. 1, 4, Eq. (1)/Fig. 3 |
| `C`, `C_perp` | subspaces of oscillator Hilbert space | cat subspace and all states outside it; gap approximately `4 K alpha^2` | PDF p. 4, Fig. 3 |
| `P_C` | projector onto cat subspace | `ket(0)bra(0)+ket(1)bra(1)`, equivalently the even/odd cat projector | PDF p. 6, Sec. III.B.1 |
| `H_CX` | time-dependent two-oscillator Hamiltonian | implements bias-preserving CX by conditionally rotating target coherent states | PDF p. 6, Eq. (2), visually checked |
| `M_X` | projective X-basis measurement | implemented by `S`, `X(pi/4)`, controlled displacement, and homodyne readout | PDF pp. 6-7, Figs. 5-6 |
| `P_plus` / preparation | ancilla preparation operation | paper says `M_X` is used for preparation; post-readout inverse rotations return the measured state to an X eigenstate | PDF pp. 5-7, Sec. III.B and Fig. 6 |
| `kappa_1` (`kappa` in plots) | single-photon loss rate | loss/gain Lindblad rate; plotted relative to `K` | PDF pp. 9-12, Sec. IV.B/Fig. 8 |
| `n_th` | thermal photon population | fixed to `8%` for the reported Kerr-cat thresholds | PDF pp. 9-12, Tables I-II/Fig. 8 |
| `kappa_2` | engineered two-photon dissipation rate | set to `K/10` in threshold models to reduce leakage | PDF pp. 9-11 |
| `D[a]` | Lindblad dissipator notation | used for photon loss/gain/two-photon dissipation; its general formula is not redefined in the paper | PDF p. 9, Sec. IV.B |
| `E_s` | syndrome-conditioned logical channel | 4-by-4 chi matrix in the small-code exact simulator | PDF p. 17, Appendix A.2 |
| `L` in Eq. (A1) | candidate logical Pauli correction | chosen from `{I,X,Y,Z}` to minimize distance to identity | PDF p. 17, Eq. (A1), visually checked |

The symbol `L` in Eq. (A1) is a logical correction, **not** a Liouvillian. The paper uses
calligraphic `L[rho]` for dissipative evolution in prose/Table II, but nowhere defines the
project's proposed per-touch channel `exp(L/4)`.

## Method (deep) [paper]

### XZZX check and syndrome

Each bulk face has stabilizer `S_f=XZZX`. Fig. 2(b), PDF p. 3, visually shows a face ancilla
prepared in `|+>`, four ordered two-qubit interactions, and an `X` measurement. Combining Fig. 2
with the round-time statement on PDF p. 12, an XZZX check uses two CX and two CZ gates. All checks
are interleaved in parallel in the Pauli simulation; the small exact simulation instead completes
one check and reuses one ancilla before moving to the next check (Appendix A.2, PDF p. 17).

Consecutive outcomes define a defect through `S_f(t-1)S_f(t)=-1`. The threshold simulation starts
from a noiseless code state, applies `d_z` noisy extraction rounds, adds one noiseless final round,
decodes the observed syndrome, and counts whether sampled error and correction differ by a logical
operator (PDF pp. 7-8 and Appendix A.1, pp. 16-17).

### Kerr-cat carrier and operations

The elementary physical object is an infinite-dimensional two-photon-driven nonlinear oscillator:

```text
H_cat = -K a^dagger^2 a^2 + K alpha^2 (a^dagger^2 + a^2).   (1)
```

Its logical cat subspace is separated from excited oscillator states by a gap approximately
`4K alpha^2` (PDF p. 4, Fig. 3). The paper gives gate-specific Hamiltonians and durations: for
example, `T_CZ=pi/(8 J alpha^2)` and the time-dependent `H_CX` of Eq. (2). These are physical
gate-duration evolutions, not equal quarter-slices of a common Liouvillian.

### Measurement and reinitialization

Fig. 6, PDF p. 7, visually specifies:

```text
X-basis measurement: S -> X(pi/4) -> controlled displacement -> homodyne.
post-measurement preparation: X(pi/4)^dagger -> S^dagger.
```

The text says the measured ancilla is projected into `|0>` or `|1>` conditional on the homodyne
outcome, and the inverse rotations reinitialize it into `|+>` or `|->` for the next syndrome
round. This is explicit evidence for a **measurement-conditioned re-preparation into the
corresponding X eigenstate**. It is not, by itself, an unconditional reset channel that forces
every branch to a single fixed `|+>` state; an additional feedback/relabel convention would be
needed if that exact boundary state is required.

### Noise-channel derivation and leakage deletion

The physical gate simulations use thermal photon loss/gain

```text
kappa_1(1+n_th) D[a] rho + kappa_1 n_th D[a^dagger] rho,
```

and add `kappa_2 D[a^2]rho` to cool population outside the cat manifold (Sec. IV.B, PDF pp. 9-10).
The CX is simulated in two stages: Hamiltonian evolution with loss/gain, then uncoupled cats with
two-photon dissipation. Measurement uses master-equation simulations for `X(+/-pi/4)` and
`S^(dagger)`, followed by stochastic-master-equation simulation of controlled displacement and a
`60%`-efficient homodyne measurement.

The paper then states the crucial truncation explicitly (PDF p. 10, visually checked): leakage is
suppressed at the physical-operation level, but **residual leakage is neglected in the subsequent
surface-code simulations**. The reported scope is `10^-3` to `10^-4` leakage probability per
qubit per stabilizer round; Tables I-II separately report `~10^-4` to `10^-5` per operation. These
are different scopes, not interchangeable values. The large-code simulation Pauli-twirls the
resulting computational-subspace channels. The small-code exact simulation also treats strict
two-level qubits and explicitly neglects residual leakage (PDF p. 13).

## The MECHANISM [paper]

The paper's leakage is population outside the bosonic Kerr-cat subspace `C` of a driven nonlinear
oscillator. Thermal excitation and drive-induced virtual transitions can populate `C_perp`;
engineered two-photon dissipation cools that population. This mechanism has oscillator ladder
operators, a cat-manifold gap, and gate-specific driven Hamiltonians.

That object is not transmon-qutrit leakage among `|0>`, `|1>`, and `|2>`, and the paper never
defines qutrit seepage/heating rates or a qutrit data/ancilla reset map. References to transmons on
PDF pp. 5, 12, and 16 are comparisons or external coupler/readout contexts, not the simulated
carrier.

## Mechanism mapping to error_coupling_simulator [ours]

- **Reusable:** XZZX check orientation; the ancilla/data gate order in Fig. 2; consecutive-round
  detector construction; explicit measurement/re-preparation structure as a circuit-design clue.
- **Not reusable without a new derivation:** Kerr-cat oscillator Hamiltonians and numerical values
  cannot be relabeled as transmon-qutrit rates.
- **Missing bridge:** the paper does not derive `RunSpec(theta,g_seep,g_heat)`, a qutrit
  Liouvillian, or a per-touch `exp(L/4)` channel.
- **Critical mismatch:** the paper intentionally deletes residual leakage before its XZZX
  threshold/record simulation. It therefore cannot validate a carrier whose scientific purpose
  is to retain leakage transport and coherence through all rounds.

## The OBSERVABLE / metric [paper]

The large-system observable is decoder logical failure rate and threshold. The small-system exact
simulator computes a logical chi matrix `E_s` conditioned on a fixed syndrome `s`, then chooses

```text
argmin_{L in {I,X,Y,Z}} || L o E_s - I ||.                  (A1)
```

The threshold simulations necessarily sample syndrome histories, but the paper aggregates them
through a decoder. It does not expose or score the complete joint distribution of all syndrome
bits and the logical observable, and it reports no full-record TV/KL/NLL or retained shot-level
record artifact. A syndrome-conditioned logical channel is not the same object as a full joint
multi-round record law.

## Findings + numbers [paper]

| result | value | exact location |
|---|---:|---|
| generic biased XZZX threshold with bias-preserving CX (`zeta=100`) | `p_z=0.98+/-0.05%`, about `2.1%` CX error | PDF p. 9, Fig. 7 and text |
| `alpha^2=6.25` Kerr-cat threshold | `kappa/K ~ 2.5e-4` | PDF pp. 11-12, Fig. 8 |
| corresponding bias-preserving CX threshold | approximately `6.5%` infidelity | PDF pp. 11-12, Fig. 8/text |
| average CX bias at that threshold | approximately `351` | PDF p. 12 |
| example lifetime for `K/(2pi)=10 MHz` | greater than `63.6 microseconds` | PDF pp. 11-12 |
| residual leakage after physical suppression | `10^-3` to `10^-4` per qubit per stabilizer round | PDF p. 10 |
| leakage listed per individual operation | approximately `10^-4` to `10^-5` | PDF pp. 10-11, Tables I-II |
| two-photon dissipation effect after each CX | leakage reduced by factor approximately `10` | PDF p. 10 |

These numbers are specific to the paper's Kerr-cat model and assumptions. None is a paper-measured
transmon-qutrit parameter.

## Limitations [paper]

- Residual leakage is explicitly neglected in both large surface-code threshold simulations and
  small-code exact simulations (PDF pp. 10 and 13).
- Large-code simulations Pauli-twirl master-equation-derived channels.
- The exact small-code simulator sequentializes checks and reuses one ancilla, changing error
  propagation relative to the parallel circuit; the authors describe the idle-noise matching as
  only roughly equivalent (PDF p. 17).
- The CX master equation is a two-step conservative approximation because time-dependent
  two-photon dissipation is difficult to simulate (PDF pp. 9-10).
- Pulse shaping is absent; crosstalk, drive-induced heating, and additional leakage in larger
  systems are deferred (Discussion, PDF p. 16).
- Full resource estimation is deferred.
- The paper's statement on PDF p. 18 that Kerr-cat S-gate “infidelity can be significantly higher”
  than the dissipative-cat case conflicts with the surrounding claim of higher Kerr-cat fidelity
  and with Fig. 10's plotted lower blue infidelity. This appears to be a textual sign error/typo;
  the ambiguity is preserved here rather than silently corrected.

## Contrary evidence and failure regimes [paper]

- A lower-infidelity but non-bias-preserving `CX_R` gate lowers the threshold by about `40%`
  relative to the bias-preserving CX (PDF pp. 11-12). Total gate fidelity alone is insufficient.
- For the CSS surface code in the tested high-bias Kerr-cat region, logical error remains near
  `50%` and does not improve with size (PDF p. 12).
- The repetition code retains logical coherence: its full physical noise performs about `10%`
  worse than its Pauli twirl in one tested small-code setting, and off-diagonal logical-chi terms
  can exceed dominant diagonal terms (PDF p. 15). The paper's favorable Pauli-twirl finding for
  the surface-code variants is not universal.
- The explicit leakage omission directly opposes any claim that the reported XZZX threshold
  includes coherent leakage propagation.

## Project kill conditions [ours]

This source kills, rather than supports, any assertion that the reported `6.5%` threshold or its
syndrome histories were obtained with residual leakage retained through the full code: the paper
says the opposite. It also cannot ground a transmon-qutrit rate tuple or `exp(L/4)`. A project use
is admissible only if it is labelled as XZZX circuit geometry, Kerr-cat-specific component
evidence, or a cautionary leakage-deletion precedent—not as a direct physical bridge for the
project carrier.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| four XZZX data qubits plus face ancilla `ket(+)` | ordered two-CX/two-CZ parity circuit; measure ancilla in `X` | circuit elements act within computational cat subspace | one check outcome | PDF p. 3, Fig. 2; p. 12 round-time comparison | `matched` |
| homodyne-conditioned ancilla in `ket(0)` or `ket(1)` | `X(-pi/4)` then `S^dagger` | measurement branch is known | corresponding `ket(+)` or `ket(-)` state for next round | PDF p. 7, Fig. 6 and adjacent text | `matched` |
| measured branch | force every branch to the same fixed `ket(+)` state | would require explicit feedback/relabel | unconditional fixed-state reset | not specified | `unsupported` |
| driven Kerr oscillators plus thermal loss/gain | gate-specific Hamiltonian/master-equation evolution | truncation chosen so leakage is smaller than total infidelity | noisy computational-subspace gate channel plus residual leakage estimate | PDF pp. 4, 6, 9-11; Eqs. (1)-(2), Tables I-II | `matched` |
| residual population in `C_perp` | engineered two-photon dissipation | `kappa_2=K/10` in threshold model | reduced leakage | PDF pp. 9-10 | `matched` |
| reduced-leakage physical operation | delete residual leakage, Pauli-twirl channel | large-code tractability | circuit-level Pauli XZZX simulation | PDF pp. 8, 10-11 | `matched` |
| transmon qutrit plus common Liouvillian `L` | apply `exp(L/4)` at each touch | no such model/normalization in paper | qutrit leakage record | nowhere in full text | `unsupported` |
| `d_z` noisy rounds plus final readout | decode sampled syndrome and count logical mismatch | aggregation through MWPM/optimal decoder | LER and threshold | PDF pp. 7-12; Appendix A pp. 16-17 | `matched` |
| complete syndrome/observable trajectory | retain and score joint probability | not done | full-joint record oracle | nowhere in full text | `unsupported` |

The replay succeeds for the Kerr-cat component chain only after the explicit residual-leakage
deletion. It fails for the project's qutrit-to-full-record bridge.

## Relevance to error_coupling_simulator [ours]

This is stronger circuit evidence than a purely phenomenological XZZX paper: Fig. 2 and Fig. 6
make ancilla interaction, readout, and branch-conditioned re-preparation auditable. It also forces
a correction to any overbroad citation: the paper's physical carrier is a bosonic Kerr-cat and its
surface-code simulation discards the very residual leakage the project wants to preserve. The
paper therefore supports the **circuit shell**, not the project's qutrit leakage dynamics,
quarter-slice normalization, or full-record faithfulness.

## How to use / trust + open questions [ours]

**Trust level:** complete full-text read of a pinned version; all assigned circuit, carrier,
leakage-deletion, threshold, and conditional-logical-channel pages visually checked. The temporary
artifacts were intentionally not persisted, so future load-bearing reuse should reacquire `v2` and
verify the recorded SHA-256.

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| XZZX stabilizer and ancilla parity circuit | PDF p. 3, Fig. 2 | `XZZX` face, ancilla `ket(+)`, ordered entangling gates, `X` readout | no transmon-qutrit carrier | `closed` |
| measurement-conditioned X-basis re-preparation | PDF p. 7, Fig. 6/text | inverse rotations map post-readout branch to `ket(+)` or `ket(-)` | no explicit branch-erasing fixed-`ket(+)` reset | `closed` for conditional re-preparation |
| deterministic fixed-state ancilla reset | full text | nothing beyond branch-conditioned re-preparation | no unconditional CPTP reset map | `missing` |
| Kerr-cat leakage mechanism | PDF pp. 4, 9-10, Eq. (1)/Sec. IV.B | leakage leaves cat subspace and is cooled by two-photon dissipation | no qutrit `ket(2)` model | `closed` only for Kerr-cat leakage |
| residual leakage through full XZZX rounds | PDF pp. 10 and 13 | residual leakage is neglected | it is not propagated to the reported record/LER | `contradicted` |
| transmon-qutrit leakage bridge | full text | transmons appear only as comparisons/context | no qutrit rates or generator | `missing` |
| `exp(L/4)` quarter-touch normalization | full text; Eqs. (1)-(2), gate times checked | gate-specific durations and evolutions | no common quarter-slice channel | `missing` |
| full joint multi-round record law/oracle | PDF pp. 7-8, 16-17 | histories are decoded into LER; `E_s` is syndrome-conditioned | no `P(record)`, TV/KL/NLL, or shot artifact | `missing` |

**`read_status: complete`**

**`evidence_status: persisted`**
