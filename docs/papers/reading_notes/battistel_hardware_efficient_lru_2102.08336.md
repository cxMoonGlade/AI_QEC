# Full-text review — Battistel, Varbanov, Terhal, “A hardware-efficient leakage-reduction scheme for quantum error correction with superconducting transmon qubits” (arXiv:2102.08336v2)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** Version-pinned arXiv PDF
> `2102.08336v2` was acquired temporarily with
> `.agents/skills/deep-read-paper/scripts/fetch_and_extract.py`; the repository does not retain the PDF or
> derived text. PDF signature/head/tail verified; **24 pages**, **1,073,052 bytes**, SHA256
> `6ad65e89e83694f902eca300415ef5cf1975256d3feb858fcb00f853d85a60ea`.
> PyMuPDF extraction (108,923 characters; one extraction null byte) was used only for navigation. The entire
> paper, Appendices A–C, and references were traversed. PDF pages **3–10 and 18–21** were rendered at 150 dpi
> and visually inspected. In particular: the physical `|20> <-> |01>` res-LRU object (Fig. 1; Eqs. 5–10),
> the Surface-17 repeated circuit and LRU placement (Fig. 3), the measurement-conditioned ancilla pi-LRU and
> readout matrix (Eq. 17), leakage/seepage rates and lifetime model (Eqs. 18–25; Fig. 4), logical-error metric
> (Fig. 5), the phenomenological production-map jump operators (Eqs. C1–C2), simulation parameters (Table II),
> and the conditional-phase failure regime (Fig. 10) were checked against rendered pages. The arXiv record
> says v2 was submitted 6 Jul 2021; the PDF prints 7 Jul 2021 and links to **PRX Quantum 2, 030314 (2021),
> DOI `10.1103/PRXQuantum.2.030314`**, published 26 Jul 2021. The publisher-layout PDF was not independently
> hash-compared. The appendices are included in this 24-page artifact; no separate supplement was assumed.
> The paper points to data/analysis at `10.4121/c.5320331`, pulse-optimization code at `10.4121/14762052`,
> and says the simulation-generation code is available on request; those external artifacts were not needed
> for, and were not audited in, this source-local reading.

## Metadata [paper]

- **Authors / affiliations.** F. Battistel and B. M. Varbanov (QuTech, TU Delft); B. M. Terhal (QuTech and
  JARA Institute for Quantum Information), PDF p. 1.
- **Venue / status.** arXiv:2102.08336v2; PRX Quantum **2**, 030314 (2021), DOI
  `10.1103/PRXQuantum.2.030314`.
- **Type.** Theory, pulse modeling, Lindblad simulation, and full density-matrix Surface-17 simulation; it
  proposes hardware operations but does not experimentally demonstrate them.
- **Primary objects.** A resonator-assisted data-qutrit leakage-reduction unit (`res-LRU`), a measurement-
  conditioned ancilla-qutrit `|1> <-> |2>` pi pulse (`pi-LRU`), and their insertion into a repeated rotated
  distance-3 surface-code schedule.

## Executive summary [paper]

[paper] The proposed data-qubit res-LRU drives the effective transmon–resonator transition
`|20> <-> |01>`; resonator decay then carries the leaked population to `|00>` (Fig. 1, pp. 2–3). A Lindblad
pulse study gives a selected operating point with about 99.5% leakage reduction and about 0.25% average
induced leakage, under the specified device model (Fig. 2, pp. 4–6). For measured ancillas, the paper instead
uses the qutrit readout declaration and conditionally applies a `|1> <-> |2>` pi pulse when the declared result
is `|2>` (Secs. II A–B, pp. 7–8). Density-matrix simulations insert these operations into every 800 ns
Surface-17 cycle (Fig. 3) and find that average leakage lifetimes fall from at least 10 cycles to approximately
one; at the chosen parameters the simulated logical error rate falls by as much as 30% relative to no LRUs
(Figs. 4–5, pp. 9–10).

[paper] The ancilla pi-LRU is a **measurement-conditioned leakage return**, not an unconditional reset of all
ancilla states to `|0>`: a correctly declared actual `|2>` is rotated to `|1>`, while declaring an actual `|1>`
as `|2>` makes the same pulse induce leakage (Sec. II B 2, p. 8).

## Selection + coverage [ours]

[ours] Assigned Charter-B rows:

- an explicit qutrit ancilla measurement/declaration/conditional-feedback instrument in a repeated QEC cycle;
- a qutrit leakage/seepage object and an explicit Surface-17 schedule;
- observable definitions for leakage lifetime, steady state, and logical error;
- negative boundary checks: XZZX, physical `exp(L/4)`, a jointly calibrated project parameter cell, full joint
  `{det,obs}`, and a literature-fixed finite history cutoff.

[ours] The source is component-direct for explicit ancilla measurement-conditioned leakage removal and for a
conventional rotated-surface-code qutrit simulation. It is not a direct source for the project's combined
Charter-B bridge. No contrary source was assigned inside this single-paper read; Ghosh et al. 2013 is read in
a separate note and supplies an explicit per-cycle `|0>` reset for a much smaller single-check circuit.

## Notation + source-location ledger [paper]

| symbol | domain / type | fixed or variable | meaning and assumptions | exact source location |
|---|---|---|---|---|
| `a`, `b` | bosonic annihilation operators | fixed roles | readout resonator and transmon mode | Eqs. (1)–(4), p. 2 |
| `omega_r,omega_q,omega_d` | angular frequencies | device/drive parameters | resonator, transmon, drive | Eqs. (1)–(4), p. 2 |
| `alpha<0`, `g`, `Omega`, `phi` | frequency/coupling/drive parameters | swept except `phi=0` | transmon anharmonicity, capacitive coupling, drive amplitude and phase | Eqs. (1)–(4), p. 2 |
| `ket(i,j)` | joint basis | indices are transmon, resonator | e.g. leaked transmon `ket(2)` plus zero photons is `ket(2,0)` | Fig. 1 and Sec. I A, pp. 2–3 |
| `tilde g` | effective coupling | drive dependent | coupling between `ket(2,0)` and `ket(0,1)`; lowest-order formula proportional to `Omega g alpha` | Eqs. (9)–(10), p. 3 |
| `kappa` | rate | fixed per device model | resonator energy-relaxation rate; `kappa/2pi=10 MHz` at Table-I point | Fig. 1; Table I, pp. 3–4 |
| `R` | probability in `[0,1]` | LRU performance parameter | leakage-reduction rate, `1-p_f^(2)` given a fully leaked input | Sec. II B 1; Eq. (16), p. 7 |
| `L_1^LRU` | probability | LRU-induced error parameter | average induced leakage from equally weighted `ket(0)`/`ket(1)` inputs | Sec. II B 1; Eq. (16), p. 7 |
| `M_ij=p^M(i given j)` | stochastic matrix | selected readout model | declared qutrit outcome `i` conditioned on actual postmeasurement state `j` | Eq. (17), p. 8 |
| `L_1,L_2` | per-CZ probabilities | swept/imported error model | average leakage and seepage of a CZ; `L_1` scanned to 0.5% | Sec. II B; Eqs. (18)–(19), pp. 7–8 |
| `Gamma_{C->L},Gamma_{L->C}` | probabilities per QEC cycle | effective Markov rates | computational-to-leakage and leakage-to-computational transitions; `L` is one-dimensional `ket(2)` | Sec. II C; Eqs. (18)–(23), pp. 8–9 |
| `l_avg^L` | QEC cycles | fitted/derived | mean duration of a leakage episode, `1/Gamma_{L->C}` in the classical Markov model | Eqs. (20)–(21), p. 8 |
| `bar p_L(n), bar p_ss^L` | probabilities | averaged/fitted | leakage population at cycle `n` and its steady state | Eqs. (22)–(23), p. 9 |
| `F_L(n), epsilon_L` | probabilities | fitted per condition | logical fidelity and logical error rate per QEC cycle | Sec. II D, pp. 9–10 |
| `phi_flux^L,phi_stat^L` | angles | randomized/fixed in a simulation set | leaked-neighbour conditional phases for which member of a CZ pair is leaked | App. C 3, pp. 20–21 |

## Method (deep) [paper]

### Physical data-qutrit res-LRU

[paper] In a common rotating frame, the transmon-resonator Hamiltonian is

```text
H  = H0 + Hc + Hd,                                               Eq. (1), p. 2
H0 = delta_r a^dagger a + delta_q b^dagger b
     + alpha/2 (b^dagger)^2 b^2,                                Eq. (2)
Hc = g(a b^dagger + a^dagger b),                                Eq. (3)
Hd = Omega/2 (exp(i phi)b + exp(-i phi)b^dagger).                Eq. (4)
```

[paper] Two virtual paths through `|11>` and `|10>` generate the effective `|20> <-> |01>` coupling shown
in Fig. 1. The visually checked lowest-order result is

```text
tilde g approximately Omega g alpha / [sqrt(2) Delta(Delta+alpha)], Eq. (10), p. 3.
```

The coupling vanishes for a harmonic system (`alpha=0`) by destructive interference. Appendix A gives the
Schrieffer-Wolff expansions and their higher-order corrections; the pulse simulation itself uses exact
diagonalization of `H0+Hc` and does not replace the physical Hamiltonian by the low-order expression.

[paper] The pulse envelope is the rise–flat–fall `sin^2` schedule in Eq. (11), with amplitude, frequency,
duration and rise time optimized. The open-system evolution is the Lindblad equation (12) with dressed
relaxation/dephasing jump operators (14)–(15). At the chosen Table-I model point,

```text
Omega/2pi approximately 204 MHz, omega_d/2pi approximately 5.2464 GHz,
t_p=178.6 ns, residual leaked population approximately 0.5%,          Fig. 2, pp. 4–6.
```

Thermal resonator occupation also drives the reverse `|01> -> |20>` process, yielding about 0.48% induced
leakage from `|0>` at `bar n=0.005`; this is not a perfect one-way reset.

### Production Surface-17 map

[paper] The full resonator is not included in the Surface-17 density matrix. It is traced out and the res-LRU
is modeled as incoherent `|2> -> |0>` plus possible `|0> -> |2>` excitation (Sec. II B 1, p. 7). For
populations before/after the operation,

```text
p_f^{|2>} approximately (1-R) p_i^{|2>} + 2 L_1^LRU p_i^{|0>},   Eq. (16), p. 7.
```

Appendix C implements this phenomenological map using PTMs and Lindblad jump operators proportional to
`|0><2|` and `|2><0|` (Eqs. C1–C2, pp. 18–19; visually checked). It is therefore important to distinguish the
physical transmon-resonator model from the reduced production channel used in the full-code simulation.

### Explicit ancilla measurement-conditioned pi-LRU

[paper] The dispersive readout yields an IQ-plane point, which is declared as `|0>`, `|1>`, or `|2>`. The
paper assumes a resolvable `|2>` cluster and sufficiently fast classical feedback. A declared `|2>` triggers
a 20 ns `|1> <-> |2>` pi pulse at the end of photon depletion (Sec. II B 2; Table II, pp. 8,20).

[paper] The readout/declaration model is

```text
M = [[1, 0, 0],
     [0, pM(1|1), 1-pM(1|1)],
     [0, 1-pM(2|2), pM(2|2)]],                                Eq. (17), p. 8.
```

Thus false `1 -> declared 2` events make the pi pulse induce leakage; false `2 -> declared 1` events let
leakage persist. Computational-subspace declaration errors and actual `0 -> declared 2` are omitted by
assumption. Delaying feedback to the following cycle is discussed but not simulated.

### Repeated code experiment

[paper] Figure 3 (visually checked p. 6) is a rotated distance-3 **Surface-17** layout with separate X- and
Z-type ancillas. The schedule interleaves their parity-check units. Res-LRUs are unconditional on the three
high-frequency data qutrits after their CZs; pi-LRUs are conditioned on the ancilla measurement outcome.
The cycle duration is 800 ns (Sec. II A; Table II). The simulation uses qutrits only for leakage-prone sites,
qubits elsewhere, relaxation/dephasing, a per-CZ leakage model imported from Varbanov et al., and fixed random
leakage conditional phases (Sec. II B, App. C 3).

## The MECHANISM [paper]

[paper] In the full device-level res-LRU, a microwave drive couples a leaked transmon state `|20>` to a
one-photon resonator state `|01>`; fast resonator decay maps that population to `|00>`. In the full-code
reduced model, this becomes an incoherent qutrit seepage operation plus induced leakage. For ancillas, qutrit
readout followed by conditional feedback returns a correctly detected `|2>` to `|1>`.

[paper] Leakage in the Surface-17 noise model is generated principally by flux-pulsed CZs. The paper scans
`L_1<=0.5%` per CZ, assumes single-qubit-gate leakage negligible, omits further `|2> -> |3>` leakage, and
sets computational–leakage coherences to zero in the imported model. A leaked qubit persists and applies
conditional phases to nonleaked CZ partners until seepage/LRU action returns it.

## Mechanism mapping to AI_QEC [ours]

[ours] The source directly licenses a component-level statement: explicit ancilla qutrit readout, declaration
errors, and outcome-conditioned leakage removal can be inserted into a repeated conventional surface-code
instrument. It also demonstrates that “reset” must specify its target state and false-trigger behavior.

[ours] It does not map the project's static local generator `(theta,g_seep,g_heat)` to a physical transmon CZ.
Its `L_1` and `L_2` are per-CZ probabilities in an imported qutrit error model; its production res-LRU is a
different Lindbladian constructed specifically for leakage removal. No `exp(L/4)` appears.

## The OBSERVABLE / metric [paper]

### Leakage lifetime and steady state

[paper] With a two-state classical Markov reduction `C <-> L`, the source uses

```text
Gamma_{C->L} approximately N_flux L_1,                           Eq. (18), p. 8
Gamma_{L->C} approximately N_flux L_2 + [1-exp(-t_c/(T1/2))],    Eq. (19)
l_avg^L = 1/Gamma_{L->C},                                       Eqs. (20)–(21)
bar p_L(n) = Gamma_{C->L}/(Gamma_{C->L}+Gamma_{L->C})
             * [1-exp(-(Gamma_{C->L}+Gamma_{L->C})n)],           Eq. (22), p. 9
bar p_ss^L = Gamma_{C->L}/(Gamma_{C->L}+Gamma_{L->C}).           Eq. (23)
```

The paper fits per-qubit `bar p_L(n)` from 20-cycle Surface-17 runs and reports lifetime and steady-state
curves in Fig. 4. These are latent/population summaries, not a complete classical detector-record law.

### Logical error

[paper] With initial state `|0>_L`, logical fidelity is fitted as

```text
F_L(n) = [1 + (1-2 epsilon_L)^(n-n0)]/2,
```

where `epsilon_L` is the logical error rate per QEC cycle (Sec. II D, p. 9). Results are given for an
upper-bound decoder that accesses density-matrix information and for MWPM using syndrome information. The
paper does not run the corresponding `|+>_L` experiment and does not expose a joint probability table over
all multi-round syndromes/detectors and final logical observables.

## Findings + numbers [paper]

| finding | value / regime | exact source |
|---|---|---|
| selected physical res-LRU operating point | `Omega/2pi≈204 MHz`, `omega_d/2pi≈5.2464 GHz`, `t_p=178.6 ns` | Fig. 2; Sec. I B, pp. 4–6 |
| physical-model leakage reduction / induced leakage | `R≈99.5%`, `L_1^LRU≈0.25%` at `bar n=0.005` | Eq. (16) interpretation, pp. 6–8 |
| Surface-17 cycle | 9 data + 8 ancilla; 800 ns; explicit repeated circuit | Fig. 3, pp. 6–7; Table II, p. 20 |
| code-simulation LRU point | `R=95%`, `L_1^LRU=0.25%`, `pM(2 given 2)=90%`, `pM(1 given 1)=99.5%` | Sec. II D; Fig. 5, pp. 9–10 |
| average leakage lifetime | falls from `>=10` cycles to approximately one for strong-enough LRUs | Fig. 4, p. 9 |
| logical error reduction | up to about 30% versus no LRUs at the tested `d=3` points | Fig. 5, p. 10 |
| sampling per main condition | `2 x 10^4` runs of 20 QEC cycles | Figs. 4–5 captions, pp. 9–10 |
| conditional-phase sensitivity | random phases perform near the `pi/2` worst case; setting phases to zero can rival random-phase LRUs, though LRUs still help | Fig. 10, pp. 20–21 |

## Limitations [paper]

- [paper] This is a proposal/simulation, not an experimental demonstration of either LRU.
- [paper] Only distance 3 is simulated; the authors explicitly say they cannot estimate a threshold and only
  expect improved large-distance behavior (pp. 2, 11).
- [paper] The code is a conventional rotated Surface-17 circuit with X- and Z-type checks, not XZZX (Fig. 3).
- [paper] Leakage-prone sites have three levels, other sites two; further `|2> -> |3>` leakage is omitted
  because the authors expect LRUs to keep `|2>` short-lived (p. 7).
- [paper] The full resonator is absent from the full-code simulation; res-LRU is replaced by an approximate
  incoherent qutrit map (p. 7, App. C 1).
- [paper] The pi-LRU relies on distinguishable qutrit readout and 200–300 ns real-time declaration/feedback;
  delayed variants are discussed but not simulated (p. 8).
- [paper] The readout matrix omits computational-subspace declaration errors and assumes no actual
  `|0> -> declared |2>` event (Eq. 17).
- [paper] The logical study initializes only `|0>_L`; similar performance for other states is expected rather
  than demonstrated (p. 9).
- [paper] Conditional phases are selected randomly and fixed across each simulation set, not measured values
  for a jointly specified device (pp. 7,20–21).
- [paper] The reported metrics are leakage populations/lifetime, logical fidelity/error, and decoder outputs;
  no full joint multi-round `{det,obs}` law or proper-scoring-rule comparison is reported.

## Contrary evidence and failure regimes [paper]

- [paper] The res-LRU is not one-way: thermal resonator population can rotate `|01>` back to leaked `|20>`;
  colder resonators are required to reduce this induced leakage (Fig. 2, pp. 4–6).
- [paper] False pi-LRU triggers can create leakage, while missed `|2>` declarations prolong it (p. 8).
- [paper] A perfect LRU cannot make steady-state leakage zero because CZs generate leakage before the LRU;
  the floor is approximately `N_flux L_1` plus LRU-induced leakage (Fig. 4, p. 9).
- [paper] LRUs convert leakage at best into ordinary computational errors, so logical error does not return to
  the `L_1=0` value (Sec. II D, pp. 9–10).
- [paper] Performance depends strongly on leakage conditional phases; random phase choices are close to the
  tested worst case (Fig. 10, pp. 20–21).
- [paper] Short lifetime is not a theorem of the native device: without LRUs the imported model gives
  10–15-cycle average leakage, and large-code threshold claims remain expectations (pp. 8,11).

## Project kill conditions [ours]

- [ours] Do not cite this paper for an unconditional ancilla reset to `|0>`: its new ancilla operation is a
  declared-`|2>`-conditioned `|1> <-> |2>` pulse, ideally returning leakage to `|1>`.
- [ours] Do not identify its physical res-LRU Hamiltonian, its reduced res-LRU PTM, and the imported per-CZ
  leakage model as one object; the paper explicitly uses different levels of modeling.
- [ours] Do not claim XZZX, `exp(L/4)`, a full joint record, or a calibrated project tuple from this source.
- [ours] A fixed short temporal truncation must fail if it is shorter than the tail needed to reproduce the
  unmitigated 10–15-cycle lifetime regime; the paper does not prescribe a universal cutoff.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| leaked transmon `ket(2)` plus thermal resonator | evolve under Eqs. (1)–(4) with optimized drive and Lindblad jumps | Table-I parameters; truncated 6-level transmon/3-level resonator | population transferred `ket(2,0) -> ket(0,1) -> ket(0,0)` | Fig. 1; Eqs. (1)–(15), pp. 2–6 | `matched` |
| physical res-LRU dynamics | trace resonator and parameterize qutrit populations by `R,L_1^LRU` | resonator approximately returns to ground/thermal state | reduced incoherent `ket(2) -> ket(0)` plus `ket(0) -> ket(2)` map | Eq. (16), p. 7; Eqs. C1–C2, pp. 18–19 | `matched`, explicitly approximate |
| actual postmeasurement qutrit state `j` | sample declaration `i` using `M` | selected declaration-error model | declared classical outcome | Eq. (17), p. 8 | `matched` |
| declared outcome `ket(2)` | apply `ket(1) <-> ket(2)` pi pulse | fast conditional feedback; coherent pulse fidelity comparable to a one-qubit gate | actual `ket(2)` ideally becomes `ket(1)`; false actual `ket(1)` becomes leaked | Sec. II B 2, p. 8 | `matched` |
| repeated rotated-Surface-17 state | execute Fig. 3 schedule; insert res-LRU and pi-LRU each cycle | qutrits only on leakage-prone sites; imported per-CZ model; no `ket(3)` | density matrix and true/declared ancilla outcomes per cycle | Fig. 3, pp. 6–8; Table II, p. 20 | `matched` |
| per-cycle leakage populations | fit Eq. (22) | two-state classical Markov approximation | `Gamma`, `l_avg^L`, `bar p_ss^L` | Eqs. (18)–(25), pp. 8–9; Fig. 4 | `matched` |
| decoded 20-cycle runs from `ket(0)_L` | fit `F_L(n)` and compare UB/MWPM | decoder assumptions in App. C 1 b | `epsilon_L` per cycle | Sec. II D; Fig. 5, pp. 9–10 | `matched` |
| conventional Surface-17 circuit | reinterpret as explicit XZZX qutrit instrument | no basis/schedule transformation is supplied | XZZX `{det,obs}` teacher | not in paper | `unsupported` |
| scalar per-CZ `L_1,L_2` model | derive static local `exp(L/4)` at every touched layer | no project generator or fractional-siting derivation | per-touch project channel | not in paper | `unsupported` |
| reported population and logical summaries | reconstruct full joint `P(det_{1:T},obs)` | histograms/run-level joint artifact not published in the paper | TV/KL/NLL oracle | not in paper | `unsupported` |

## Relevance to AI_QEC [ours]

[ours] Reuse three contracts: (1) ancilla measurement must distinguish actual state from declared state;
(2) “reset” must name the target and false-trigger channel; (3) a reduced full-code carrier must disclose what
physical subsystem was traced out and how the replacement channel was calibrated. The paper is a useful
component reference for an explicit conventional surface-code qutrit instrument, but it cannot validate the
project's complete XZZX teacher by citation inheritance.

## How to use / trust + open questions [ours]

- **Trust level.** Full arXiv v2 text and all included appendices read; load-bearing equations, circuits,
  tables, and figures visually checked. Publisher-layout identity and external data/code were not audited.
- **Open instrument question.** Does a project ancilla-reset convention return leaked ancillas to `|0>` or
  merely to the computational subspace, and are false declaration channels represented?
- **Open bridge question.** Can a full transmon-pair CZ oracle reproduce the proposed local project channel at
  the actual XZZX gate slots? This paper supplies no such reduction.
- **Open observable question.** Do two implementations that match `l_avg^L`, `bar p_ss^L`, and `epsilon_L`
  also match the full multi-round record law? This paper does not test that stronger claim.

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| B-I1 explicit qutrit ancilla measurement-conditioned leakage removal | Fig. 3, pp. 6–7; Sec. II B 2 and Eq. (17), p. 8 | qutrit readout/declaration followed by conditional pi-LRU is repeated in Surface-17 | no unconditional `ket(0)` reset supplied by the new pi-LRU | `closed` for the stated instrument |
| B-M1/B-M2 qutrit leakage/seepage component | Secs. I–II; Eqs. (16),(18),(19); App. C 1 | physical res-LRU and reduced qutrit channel; per-CZ leakage model in a conventional schedule | no static project cell or two-body-to-local bridge | `closed` for this model |
| B-O1 leakage lifetime/steady-state/logical summaries | Eqs. (20)–(25), Fig. 4; Fig. 5, pp. 8–10 | defines and measures these summaries over repeated cycles | no full detector/observable record distribution | `closed` for these observables |
| B-I3 explicit transmon-qutrit XZZX instrument | Fig. 3, p. 6 | conventional rotated Surface-17 with separate X/Z checks | no XZZX stabilizers or XZZX schedule | `missing` |
| B-M3 physical per-touch `exp(L/4)` | entire paper | uses scalar per-CZ leakage/seepage and separate LRU maps | no static Lindblad slice or quarter-CZ siting | `missing` |
| B-O2 full joint multi-round `{det,obs}` | Sec. II D and App. C 1 b | reports fitted logical error and decoder summaries | no joint law, TV/KL/NLL, or complete run artifact in paper | `missing` |
| B-O3 literature-fixed finite cutoff | Sec. II C; Fig. 4; Discussion p. 11 | native model can have 10–15-cycle leakage; LRUs reduce it | no universal safe history length | `missing` |

**Read status:** `complete`. **Evidence status:** `persisted` in this note. These statuses are source-local; only
the cross-source literature-closure workflow may declare a field-wide gap.
