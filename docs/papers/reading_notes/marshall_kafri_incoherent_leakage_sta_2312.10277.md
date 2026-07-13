# Full-text review — J. Marshall and D. Kafri, "Incoherent Approximation of Leakage in Quantum Error Correction" (arXiv:2312.10277)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** arXiv:2312.10277v2 PDF
> `outputs/papers/coherent_leakage_longrange_closure/2312.10277v2.pdf` (23 pages,
> SHA256 `82ddaa228d8b13e0f55a5fb1c1d18e688698698ffd102823fb0f4e47d10a6ada`) →
> `outputs/papers/coherent_leakage_longrange_closure/2312.10277v2.txt` (`pdftotext -layout`).
> Provenance record:
> `outputs/papers/coherent_leakage_longrange_closure/2312.10277v2.provenance.json`.
> PDF pages 5, 7, 9–10, and 20–22 were rendered and visually inspected for Eqs. 11, 15–17 and
> Figs. 2–3, 10–18; extracted text was used only for navigation. Tags: **[paper]** = source statement;
> **[ours]** = project inference.

## Metadata [paper]

- **Authors:** Jeffrey Marshall and Dvir Kafri.
- **Venue/status:** Physical Review Applied **23**, 054025 (published 9 May 2025),
  DOI `10.1103/PhysRevApplied.23.054025`; arXiv:2312.10277v2, 5 Mar 2025.
- **Type:** channel-construction/method paper plus quantum-trajectory simulations of repetition and
  rotated surface codes with qutrit leakage.

## Executive summary [paper]

The paper defines a channel-level **Subspace Twirling Approximation (STA)** that removes coherence
between chosen Hilbert-space sectors while preserving a strictly-incoherent channel structure. Under
a simplified repeated-stabilizer model, computational–leakage coherence decays exponentially with the
number of measurements rather than vanishing after one arbitrary circuit slice. In a pure coherent-CZ
leakage stress test, exact qutrit and STA simulations differ in leakage populations, detector-event
fractions, and leakage-added logical error; for a thermal/mixed physical model, STA is much more
accurate. The paper therefore supports a **model-, schedule-, and twirl-placement-dependent** claim,
not a universal license to pinch the state after each quarter-CZ.

## Selection + coverage [ours]

This is the closest published source to the project's disputed bridge
`computational/leakage coherence -> binary QEC record`. It closes the definition of a principled
incoherent surrogate, supplies a mechanism for measurement-induced coherence decay, and directly
compares exact and incoherent d3 surface-code simulations. It does **not** close the project's exact
per-quarter-CZ pinching or full-joint-record row. Contrary sources checked: Varbanov et al. 2020
(schedule-specific null after removing exchange coherence) and Manabe et al. 2025 (large GTA LER
failure despite matched leakage/seepage rates).

## Notation + source-location ledger [paper]

| symbol | object / domain | fixed or varied | assumptions | source |
|---|---|---|---|---|
| `H = C ⊕ L` | computational plus leakage subspaces | fixed decomposition | qutrit `C=span{ket(0),ket(1)}`, `L=span{ket(2)}` | Sec. II.C, PDF pp. 4–5 |
| `P_n` | projector onto subspace `H_n` | fixed | orthogonal resolution of identity | Sec. II.C–D |
| `E_STA` | subspace-twirled channel | derived from `E` | uniform independent sector phases | Eq. 11, PDF p. 5 |
| `Delta(K_j)=sum_n P_n K_j P_n` | block-diagonal Kraus part | derived | part of STA Kraus representation | Eq. 13, PDF p. 6 |
| `phi` | CZ phase applied to a measure qubit conditional on leaked data | varied analytically | CZ creates no new leakage; measure qubit does not leak | Sec. III.A, PDF pp. 6–7 |
| `m` | number of repeated stabilizer measurements | variable integer | other data qubits do not leak in derivation | Eqs. 15–17, PDF p. 7 |
| `p` | coherent `ket(11) <-> ket(02)` transition probability | varied | data-qubit leakage only in stress test | Sec. III.B.2, Fig. 3 |
| `eta` | qutrit nonlinearity / anharmonicity | varied in exact arm | STA is phase-insensitive by construction | Fig. 12, App. E |
| added LER | logical error probability above zero-leakage arm | measured by trajectories | same circuit/no-leak baseline subtracted | Figs. 2–3 |
| DEF | marginal detector-event fraction | measured per detector/round | not the full joint record law | Figs. 10, 14, 17–18 |

## Method (deep) [paper]

For sector phases `U(phi_bar)=sum_n exp(i phi_n) P_n`, the STA is the channel twirl

```text
E_STA = < U_hat(-phi_bar) o E o U_hat(phi_bar) >_{phi_bar}.        (Eq. 11)
```

Expanding the phase average leaves cross-sector transition Kraus terms `P_m K_j P_n` and the
block-diagonal term `sum_n P_n K_j P_n` (Eqs. 12–13). The resulting map is a strictly incoherent
operation. The paper explicitly distinguishes this construction from simply appending a dephasing
map `E -> Delta o E`: STA preserves the identity channel and is the weaker intervention.

For the repeated-stabilizer calculation, the leaked data state induces `exp(i phi Z/2)` on the
measure qubit. With no CZ-generated leakage, no measure-qubit leakage, and no leakage on the other
data qubits, the two data-side factors are

```text
L_0 = |0><0| + cos(phi/2) |2><2|,
L_1 = |1><1| + i sin(phi/2) |2><2|.
```

A change in consecutive stabilizer outcomes selects leakage (Eq. 16). Summing over length-`m`
measurement histories maps the cross-subspace coherence observables `C_c(theta)` to themselves with
amplitudes

```text
r_0(m) = cos(phi/2)^m,
r_1(m) = sin(phi/2)^m.                                           (Eq. 17)
```

Thus coherence is exponentially suppressed for generic `phi`, but the rate is schedule/phase
dependent and is not an instantaneous-zero theorem.

## The MECHANISM [paper]

- **Thermal arm:** Lindblad heating/relaxation and dephasing generate mostly incoherent leakage.
- **Pure coherent stress-test arm:** a CZ drives
  `|11> -> sqrt(1-p)|11> + exp(i phi_11,02) sqrt(p)|02>` on data qubits.
- **Mixed physical arm:** coherent CZ leakage plus thermal heating, relaxation, and dephasing with
  parameters motivated by superconducting-memory experiments (Appendix F).
- **Separate effect:** a leaked data qubit can impose a conditional phase on its partner. This is not
  the same object as the off-diagonal `|11><02|` coherence.

## Mechanism mapping to the project [ours]

The project's state pinching after every quarter-CZ is **not** Eq. 11. It changes the composed channel
at four chosen boundaries and is generally stronger than the paper's channel-level STA. A faithful
paper reproduction must first implement `E_STA` on the same frozen channel and schedule, then compare
it with exact qutrit evolution. A separate per-slice pinching arm may be used only as a deliberately
stronger ablation, not named “STA”.

## The OBSERVABLE / metric [paper]

- leakage-added logical error probability / extracted LER;
- per-qubit leakage population over rounds;
- marginal detection-event fraction (DEF);
- fidelity-decay fits in the repetition-code appendices.

These observables show that incoherent approximation error can become operational. They do **not**
compare the full joint `(detectors, logical observable)` distribution using TV, KL, JSD, or held-out
record NLL. Agreement of DEF marginals therefore cannot certify record-law equality.

## Findings + numbers [paper]

| comparison | exact | STA / surrogate | source-supported conclusion |
|---|---:|---:|---|
| thermal d3 leakage-added LER | `0.275 ± 0.012%` | `0.266 ± 0.009%` | good agreement for this thermal model (Fig. 2) |
| pure coherent d3 leakage-added LER | `0.384 ± 0.015%` | naive STA `0.404 ± 0.014%` | small but systematic operational discrepancy (Fig. 3) |
| same coherent arm, fitted thermal surrogate | `0.384 ± 0.015%` | `0.365 ± 0.010%` | population-matched thermal model improves some statistics, not exact equality (Fig. 3) |
| exact coherent arm vs nonlinearity | changes with `eta` | STA invariant to `eta` | missing phase sensitivity is a real coherent effect (Fig. 12) |

Appendix-F simulations with more physical mixed noise show close exact/STA agreement in LER and DEF,
but this is a parameter-regime result, not a universal bound.

## Limitations [paper]

- The coherence-decay derivation assumes the CZ itself does not generate leakage, the measure qubit
  does not leak, and the remaining stabilizer data do not leak.
- The pure coherent model intentionally uses strong, nonphysical leakage to expose STA failure.
- The surface-code exact comparison is d3; scalable results use the approximation.
- The reported record diagnostics are DEF marginals, not a full multi-round joint distribution.
- No theorem bounds approximation error in LER or record TV from `L1`, `L2`, process fidelity, or the
  exponential coherence factor.

## Contrary evidence and failure regimes [paper]

The pure-coherent arm is an explicit failure regime for naive STA. Exact results retain `eta`
sensitivity that STA cannot represent. Conversely, thermal and mixed arms show that retaining every
off-diagonal element is not always operationally necessary. These two results rule out both universal
claims: “coherence is always irrelevant” and “coherence must always be retained.”

## Project kill conditions [ours]

- If the project calls per-quarter state pinching “the STA”, the mapping is killed by the paper's
  channel definition and explicit `E -> Delta o E` distinction.
- If a paper-faithful exact-vs-STA reproduction passes only DEF but fails full-record TV/KL or a frozen
  decoder LER, record-faithful truncation is not licensed.
- If exact/STA differences disappear only after adding a particular thermal model, the result licenses
  that frozen model and regime only.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| channel `E`, subspaces `P_n` | random sector-phase conjugation and average | independent uniform phases | `E_STA` | Eq. 11, PDF p. 5 | matched |
| `E_STA` expansion | retain transition and block-diagonal Kraus pieces | fixed Kraus-independent channel | strictly incoherent map | Eqs. 12–13, PDF p. 6 | matched |
| repeated stabilizer instrument | contract measured ancilla histories | simplified no-new-leak model | coherence factors `cos^m`, `sin^m` | Eqs. 15–17, PDF p. 7 | matched within assumptions |
| exact coherent qutrit circuit | apply STA | d3 rotated surface code, strong coherent leakage | LER/population/DEF discrepancy | Fig. 3; App. E | matched |
| project's quarter-slice state | pinch after each slice | project-specific intervention | claimed record-null channel | no source location | unsupported |

## Relevance to AI_QEC [ours]

This paper reopens ADR 0011's statement that the coherent leakage tail is absent from the record. The
defensible replacement is: repeated stabilizer measurement can suppress this coherence, and an STA can
be accurate in specified mixed/thermal regimes, but exact coherent channels exhibit measurable d3
differences. The current custom pair-moment statistic is not a substitute for exact joint-record TV/KL
and frozen-decoder LER.

## How to use / trust + open questions [ours]

- **Trust:** high for the channel definition, analytic decay calculation, and reported simulations;
  equations and load-bearing figures were visually checked from the PDF.
- **Closed by this source:** channel-level incoherent surrogate; conditional measurement-induced decay;
  existence of both accurate and inaccurate STA regimes.
- **Missing:** equivalence of quarter-CZ pinching to STA; full joint record comparison; a bound from
  channel/state truncation to rare-event LER.
- **Cross-source status:** this note alone cannot close the project claim; the closure packet remains open.
