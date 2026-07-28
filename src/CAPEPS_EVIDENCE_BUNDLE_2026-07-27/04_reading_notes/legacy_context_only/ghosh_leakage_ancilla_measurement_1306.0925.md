# Full-text review — Ghosh, Fowler, Martinis, Geller, “Understanding the effects of leakage in superconducting quantum error detection circuits” (arXiv:1306.0925v2)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** Version-pinned arXiv PDF
> `1306.0925v2` was acquired temporarily with
> `.agents/skills/deep-read-paper/scripts/fetch_and_extract.py`; the repository does not retain the PDF or
> derived text. PDF signature/head/tail verified; **8 pages**, **220,476 bytes**, SHA256
> `d2b630d8cee32a4e1ab5302fda3e4f7cee15849577565dff9eb63a10dd10f076`.
> PyMuPDF extraction (27,169 characters) was used only for navigation. PDF pages **2–7** were rendered at
> 150 dpi and visually inspected; the load-bearing circuit (Fig. 1), two-qutrit model (Eqs. 4–8), nonideal-CZ
> generator (Eqs. 11–12), measurement-conditioned leakage map (Eqs. 15–22), and paralysis observable
> (Fig. 4; Eqs. 23–27) were checked against the rendered pages. Page 1 and the references-only page 8 were
> read in the PDF/text traversal. The arXiv record says v2 was submitted 11 Dec 2013 and links it to
> **Phys. Rev. A 88, 062329 (2013), DOI `10.1103/PhysRevA.88.062329`**. The PDF front matter anomalously
> prints “Dated: September 2, 2018”; this note does not silently reconcile that printed date with the arXiv
> version history. The publisher-layout PDF was not independently hash-compared. No supplement or code
> artifact is supplied by the paper.

## Metadata [paper]

- **Authors / affiliations.** Joydip Ghosh (Calgary/Georgia), Austin G. Fowler and John M. Martinis
  (UCSB; Fowler also Melbourne), Michael R. Geller (Georgia), PDF p. 1.
- **Venue / status.** arXiv:1306.0925v2; Physical Review A **88**, 062329 (2013), DOI
  `10.1103/PhysRevA.88.062329`.
- **Type.** Analytic model plus numerical simulation; not a hardware experiment.
- **Object.** Two capacitively coupled three-level superconducting systems, one ancilla `A` and one data
  qutrit `D`, executing repeated ancilla-assisted measurement of a single data `sigma_z` operator.

## Executive summary [paper]

[paper] Each measurement cycle explicitly resets the ancilla to `|0>`, applies `H_A`, a two-qutrit CZ,
applies `H_A` again, reads and records the ancilla, and repeats; the data qutrit is never measured or reset
(Fig. 1, PDF pp. 1–2). The CZ is modeled on the full `3 x 3` tensor-product space. Small nonadiabatic
couplings can make the measurement backaction drive the data from `|1>` to a near-unit `|2>` leakage state
(Eqs. 11–18, pp. 4–5). Once data is leaked, the phase difference `theta = xi_2 - xi_1` controls whether the
ancilla readout is randomized or “paralyzed”: at `theta mod pi = 0` it repeatedly returns `|0>` and can hide
the data error; at `theta mod pi = pi/2` outcomes are equiprobable (Eqs. 20–25, pp. 5–6). The result is a
source-local demonstration that the explicit measurement instrument and its postmeasurement state update,
not merely a static data-side parity POVM, determine the multi-cycle leakage signature.

## Selection + coverage [ours]

[ours] Assigned Charter-B rows:

- explicit qutrit ancilla **reset–entangle–measure** instrument over repeated cycles;
- a gate-level qutrit leakage object and its measurement backaction;
- a multi-round classical readout signature of long-lived leakage;
- negative boundary checks: XZZX, `exp(L/4)`, full joint `{det,obs}`, and a justified finite record cutoff.

[ours] This source is load-bearing for the instrument component because Fig. 1 and Eqs. 15–22 specify both
the classical outcome and the conditional postmeasurement data transformation. It is not a full surface-code
teacher. No competing source was assigned inside this single-paper read; Battistel et al. 2021 is being read
separately as the second component source and does not alter this source-local status.

## Notation + source-location ledger [paper]

| symbol | domain / type | fixed or variable | meaning and assumptions | exact source location |
|---|---|---|---|---|
| `A`, `D` | qutrit labels | fixed roles | ancilla and data; ordered basis is `ket(A,D)` | Fig. 1 and Sec. II A, pp. 2–3 |
| `ket(psi_D) = a ket(0)+b ket(1)` | data-qubit pure state | variable amplitudes | initial state has no `ket(2)` component | Eq. (1), p. 1 |
| `H` | `3 x 3` unitary | fixed | ordinary Hadamard on `{ket(0),ket(1)}` and identity on `ket(2)` | Eq. (2), p. 2 |
| `epsilon_i`, `eta_i`, `g` | frequencies / coupling | protocol parameters | qutrit transition frequency, anharmonicity, capacitive coupling; harmonic matrix elements assumed in `Y` | Eqs. (4)–(5), p. 2 |
| `S` | `9 x 9` Hermitian generator | fixed for a chosen gate | ideal computational CZ plus noncomputational phases `xi_1,...,xi_4`; extension outside the qubit subspace is protocol-dependent | Eq. (6), p. 3 |
| `xi_i` | phases | fixed within a run; gate dependent | dynamical phases accumulated by noncomputational channels in the adiabatic Strauch-CZ model | Eq. (7), p. 3 |
| `theta = xi_2-xi_1` | angle | variable across gate implementations | leaked-data-induced ancilla rotation angle; can change with gate time/pulse | Eq. (8), p. 3 |
| `E_1,E_2,E_3`, `lambda_m` | qutrit Kraus operators / probabilities | fixed by `Delta t,T1` | amplitude damping only; `lambda_m=1-exp(-m Delta t/T1)` | Eqs. (9)–(10), p. 3 |
| `S'` | `9 x 9` Hermitian error generator | small parameters | nonadiabatic/phase errors `chi_i,zeta_i,phi_i`; simulations set all `chi_i=zeta_i=10^-2` | Eqs. (11)–(12), p. 4 |
| `T_0,T_1,T_2` | nonlinear, outcome-conditioned maps | stochastic sequence under repetition | normalized data-qutrit transformation conditioned on ancilla result `0,1,2` | Sec. III B; Eqs. (15)–(18), p. 5 |
| `W` | cycles | random-variable mean | mean spacing between consecutive ancilla `ket(1)` outcomes during leakage; ideal estimate `csc^2(theta/2)` | Eq. (25), p. 6 |
| `W*`, `theta*` | cycles / angle | background-dependent thresholds | decoherence background and estimated boundary for detectable versus paralyzing leakage | Eqs. (26)–(27), p. 6 |

`theta` here is a CZ dynamical-phase difference. [paper] It is **not** a Lindblad coherent-leakage angle and
must not be identified with a same-named project parameter without a separate bridge.

## Method (deep) [paper]

### Explicit repeated instrument

[paper] The cycle in Fig. 1 (visually verified on PDF p. 2) is

```text
ancilla reset to |0> -> H_A -> CZ_AD -> H_A -> ancilla readout and record -> repeat,
data D: never measured or reset.
```

For an initial computational data state, the ideal circuit produces

```text
a|00> + b|11>                                                   Eq. (3), p. 2,
```

so ancilla readout projects the data into the corresponding `sigma_z` eigenstate. In the nonideal qutrit
circuit, the measurement outcome selects `T_j`; Eq. (16) gives the normalized `T_0` map explicitly. Thus the
cycle is a quantum instrument: it returns a classical result and changes the surviving data state conditional
on that result.

### Two-qutrit gate model

[paper] The Hamiltonian is

```text
H(t) = diag(0,epsilon_1,2epsilon_1-eta_1)_A
     + diag(0,epsilon_2,2epsilon_2-eta_2)_D + g Y tensor Y,       Eq. (4), p. 2,
```

with the qutrit `Y` matrix in Eq. (5). The paper fixes `epsilon_D/2pi=6 GHz`,
`eta_A/2pi=eta_D/2pi=200 MHz`, and illustrates `g/2pi=25 MHz` in Fig. 2. The intended Strauch CZ uses the
`|11> <-> |20>` avoided crossing. The computational action is CZ, while noncomputational channels acquire
model- and pulse-dependent phases `xi_i` (Eqs. 6–8, visually checked p. 3).

[paper] A separate small generator `S'` produces population-transfer and phase errors,

```text
U_CZ = exp(i S') exp(i S) approximately exp(i(S+S')),           Eq. (12), p. 4.
```

The approximation and the full matrix placement of `chi_i,zeta_i,phi_i` were visually checked on p. 4.
Population transfer probability scales as `|chi_i|^2`; the simulation point `chi_i=zeta_i=10^-2` therefore
corresponds to intrinsic errors of order `10^-4`.

### Leakage-conditioned ancilla action

[paper] In the special limit of Eqs. (13)–(17), the ancilla-`0` measurement map obeys

```text
T_0 |1> = |2>                                                   Eq. (18), p. 5.
```

When the data remains in `|2>`, only `{|02>,|12>}` is occupied. In that subspace CZ is
`diag(exp(i xi_1),exp(i xi_2))`; the two Hadamards turn the phase difference into an ancilla `x` rotation,

```text
|0>_A -> cos(theta/2)|0> + sin(theta/2)|1>,                     Eqs. (20)–(22), p. 5.
```

The paper consequently obtains `P(A=0 | data leaked)=cos^2(theta/2)`.

## The MECHANISM [paper]

[paper] Leakage is near-unit population of the data `|2>` state, generated here by nonadiabatic CZ errors
plus the nonlinear, measurement-conditioned transformation. Once leaked, the data persists for many cycles
until reverse leakage or amplitude relaxation. Its continued interaction with the measured ancilla produces
phase-dependent readout backaction. This is a two-qutrit, gate-and-instrument mechanism; it is not a static
single-qutrit channel applied independently to data sites.

[paper] The authors report no leakage propagation to the neighboring qutrit in this particular two-qutrit
model (Conclusion, p. 7). They do report that a leaked data qutrit can randomize or paralyze the measurement
qutrit and thereby create long strings of time-correlated measurement errors.

## Mechanism mapping to AI_QEC [ours]

[ours] The reusable component is the need to model the ancilla and measurement boundary explicitly when a
leaked data state can change both outcome probabilities and the conditional surviving data state. A data-only
stabilizer POVM cannot be declared equivalent merely because it has the same ideal computational-subspace
parity probabilities.

[ours] No project code path was inspected for this note. The paper provides no derivation from its Strauch-CZ
`S+S'` model to the project's static local generator `(theta,g_seep,g_heat)` and no license for per-touch
`exp(L/4)` siting.

## The OBSERVABLE / metric [paper]

[paper] The primitive observable is the complete sequential **ancilla bit trace** for one repeated `sigma_z`
measurement. Figure 4 displays selected windows of those traces with simulated leakage intervals marked.
The summary statistic

```text
W = mean number of cycles between consecutive readouts of |1>
  = csc^2(theta/2)                 (without decoherence),        Eq. (25), p. 6
```

detects the difference between randomizing leakage and paralysis. With `T1=40 us`, `T2=2T1`, and
`t_cycle=45 ns`, the simulated nonleakage background spacing is 2381 cycles; the crude Pauli-twirled estimate
is `W* approximately 2T1/t_cycle=1778`, leading to `theta*=0.04` (Eqs. 26–27).

[paper] `W` is a one-dimensional summary of a single-check record. The paper neither defines detectors as
syndrome differences nor constructs a logical observable bit, TV distance, KL divergence, or record NLL.

## Findings + numbers [paper]

| finding | value / regime | source |
|---|---|---|
| repeated decoherence-only simulation | 40,000 cycles; `T1=40 us`, `T2=2T1`, `t_cycle=45 ns` | Sec. II B and Fig. 3, pp. 3–4 |
| nonideal-gate point | all `chi_i=zeta_i=10^-2`; population-transfer errors about `10^-4` | Sec. III A, p. 4 |
| randomizing leakage | `theta mod pi=pi/2`, so `P(0)=P(1)=1/2`, `W=2` ideally | Eqs. (22)–(25), pp. 5–6 |
| ancilla paralysis | `theta mod pi=0`, so repeated ancilla result is `0`, `W=infinity` ideally | Eq. (24), Fig. 4, p. 6 |
| detectability boundary at the chosen decoherence point | estimated `theta*=0.04` | Eq. (27), p. 6 |

## Limitations [paper]

- [paper] One data qutrit and one ancilla qutrit; the measured operator is a single `sigma_z`, not a weight-4
  stabilizer and not a full code (Abstract, Sec. IV).
- [paper] The H gates are ideal and act as identity on `|2>`; readout and reset are instantaneous; decoherence
  is amplitude damping only (Secs. I–II).
- [paper] The nonideal-CZ simulation uses chosen small error parameters and arbitrary/fixed dynamical phases;
  it is not calibrated to a reported device (Secs. II A, III A).
- [paper] It treats three levels per physical system and omits `|3>` and higher levels.
- [paper] Surface/toric-code consequences in Sec. IV are extrapolations from the single-operator circuit, not
  a simulated weight-4 or multi-round surface-code result.
- [paper] It reports traces and `W`, not a complete multi-stabilizer syndrome/detector/observable law.

## Contrary evidence and failure regimes [paper]

- [paper] Leakage is not guaranteed to be easy to see: the same leaked data state produces either noisy
  outcomes or a completely paralyzed ancilla depending on `theta` (Eqs. 23–27).
- [paper] The statement that ancilla leakage itself “does not compromise fault tolerance” is conditional on
  this two-qutrit model and its readout convention (p. 5); it is not a general surface-code theorem.
- [paper] The observed absence of leakage propagation is model-specific (p. 7), not a license to omit leakage
  mobility in later CZ implementations.
- [paper] `W*` and `theta*` use a crude Pauli-twirling estimate; the paper compares it to simulation rather
  than proving a universal detectability boundary.

## Project kill conditions [ours]

- [ours] This source cannot support replacing an explicit ancilla instrument by a data-only POVM unless an
  independent test shows equality of the **conditional postmeasurement maps**, not only ideal parity outcomes.
- [ours] It cannot support XZZX, `exp(L/4)`, the project parameter tuple, or a full `{det,obs}` likelihood.
- [ours] A fixed short history cutoff is killed if it erases the long strings produced during the paper's
  many-cycle leakage intervals; the paper supplies no universal cutoff length.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| ancilla `ket(0)`, data `a ket(0)+b ket(1)` | `H_A -> CZ_AD -> H_A` | ideal computational gates | entangled state `a ket(00)+b ket(11)` | Fig. 1, Eqs. (1)–(3), pp. 1–2 | `matched` |
| arbitrary data qutrit, ancilla reset | nonideal `U_CZ=exp(iS')exp(iS)` inside the same circuit | two qutrits; chosen Strauch-CZ extension and small errors | joint qutrit state before readout | Eqs. (6)–(15), pp. 3–5 | `matched` |
| joint state before readout | project ancilla result `j`, normalize data | ideal projective readout; instantaneous reset | classical `j` plus conditional data map `T_j` | Sec. III B; Eqs. (15)–(17), p. 5 | `matched` |
| data initially `ket(1)` | special-limit `T_0` backaction | Eq. (13), `chi_1=0`, `chi_2 -> 0` | leaked data `ket(2)` | Eq. (18), p. 5 | `matched` |
| data held in `ket(2)`, ancilla reinitialized `ket(0)` | leaked-subspace CZ phases plus two H gates | `ket(22)` unoccupied/decoupled | ancilla state `cos(theta/2) ket(0)+sin(theta/2) ket(1)` | Eqs. (19)–(22), p. 5 | `matched` |
| repeated ancilla outcomes during leakage | compute inter-`1` spacing | no decoherence for exact formula | `W=csc^2(theta/2)` | Eq. (25), p. 6 | `matched` |
| this single-check instrument | relabel as explicit XZZX surface-code teacher | no source transformation exists | full `{det,obs}` law | not in paper | `unsupported` |
| full-cycle leakage channel | split into four touched-CZ slices `exp(L/4)` | no Lindblad semigroup/siting argument appears | per-touch project channel | not in paper | `unsupported` |

## Relevance to AI_QEC [ours]

[ours] Reuse the **scientific contract**, not the numerical parameters: an explicit ancilla measurement must
carry initialization/reset, gate action on leaked levels, classical outcome, and the conditional data update.
Figure 1 plus Eqs. (15)–(22) are a direct counterexample to treating ideal parity probabilities as the whole
instrument. The paper does not determine how a full XZZX schedule composes these local instruments, and its
phase `theta` must not be merged with the project's leakage-angle notation.

## How to use / trust + open questions [ours]

- **Trust level.** Full arXiv v2 text read; all load-bearing formula/circuit/figure pages visually checked.
  Publisher-layout identity and the anomalous printed 2018 date remain unverified.
- **Open implementation question.** Does the intended project ancilla model reproduce both the outcome law
  and the conditional data state for leaked inputs across the actual XZZX schedule?
- **Open observable question.** Which full-record metric detects paralysis without reducing it to `W`, and
  how sensitive is it to a finite history cutoff?

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| B-I1 explicit qutrit ancilla reset/measurement instrument | Fig. 1, pp. 1–2; Eqs. (15)–(22), p. 5 | reset–gate–readout repeats and yields outcome-conditioned data maps | no weight-4/full-code circuit | `closed` |
| B-M1 two-qutrit leakage/backaction object | Eqs. (4)–(18), pp. 2–5 | nonideal CZ plus measurement can produce persistent data `ket(2)` | no static `(theta,g_seep,g_heat)` channel | `closed` for this model |
| B-O1 multi-round leakage readout signature | Fig. 4; Eqs. (23)–(27), p. 6 | randomization/paralysis appears in sequential ancilla records | no detector/observable joint law | `closed` for one `sigma_z` record |
| B-I3 explicit transmon-qutrit XZZX instrument | Sec. IV, p. 7 | surface-code relevance is discussed qualitatively | no XZZX or simulated weight-4 check | `missing` |
| B-M3 physical per-touch `exp(L/4)` | entire paper | no such object | no Lindbladian fraction or siting derivation | `missing` |
| B-O2 full joint multi-round `{det,obs}` | entire paper | records one ancilla bit sequence | no multi-check detectors, logical observable, TV/KL/NLL | `missing` |
| B-O3 literature-fixed finite cutoff | Fig. 4 and Sec. IV | leakage can produce long time-correlated strings | no safe universal truncation length | `missing` |

**Read status:** `complete`. **Evidence status:** `persisted` in this note. These statuses are source-local; only
the cross-source literature-closure workflow may declare a field-wide gap.
