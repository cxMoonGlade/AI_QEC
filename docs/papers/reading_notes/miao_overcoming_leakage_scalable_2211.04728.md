# Full-text note — Miao, McEwen et al. (Google Quantum AI), *Overcoming Leakage in Scalable Quantum Error Correction*

> **⚠️ CORRECTION (2026-06-25, ar5iv-verified + deep-research wf_dc2e46de):** SI S1 reads
> `g_{|21⟩–|12⟩} = 2g` (**NOT √2 g**) and `g_{|30⟩–|21⟩} = √3 g`, so `g_eff = −g_{|21⟩–|12⟩}·g_{|30⟩–|21⟩}/η
> = −2√3 g²/η`, `P_t = sin²(g_eff·t)`. Any "√2 g" written below is a transcription slip from the first read —
> **use 2g**. Transport fractions re-confirmed against ar5iv: **|30⟩↔|12⟩ ≈ 18–19%**, **|31⟩↔|22⟩ ≈ 58–61%**
> (the |30-12 / |31-22 labels are correct).

> Provenance: full-text read from the PDF
> `docs/papers/miao_overcoming_leakage_scalable_2211.04728.pdf` (owner-password-only
> encryption — opens for `pdftotext -layout` / `pdftoppm` but not the Read tool; text
> extracted and all figures/tables cross-checked against rendered page images, which were
> deleted after reading; nothing new committed besides this note). Symbol mangling in the
> raw text (`�` ↦ `×`, `−`, `→`, `Λ`, `π`, `δ`, `ψ`, `θ`) was reconstructed against the
> rendered figures.
> arXiv:2211.04728v1 [quant-ph], 9 Nov 2022 (dated Nov 10, 2022). Published as
> **Nature Physics 19, 1780–1786 (2023), DOI 10.1038/s41567-023-02226-w** ("Overcoming leakage in
> quantum error correction"); the arXiv title carries "scalable." Data: Zenodo `10.5281/zenodo.7302032`.
> **CITATION FIX (2026-06-30):** the prior "Nature 638, 920–926 (2023)" here was WRONG — it conflated
> this Miao leakage paper with the *Willow* paper (Nature 638, 920–926 (2025), arXiv:2408.13687).
> Verified correct via ADS bibcode 2023NatPh..19.1780M + the journal DOI.

> **[ours] reframed 2026-07-13** — the decoder-oriented framing below ('sim-only teacher / decoding headroom above MWPM') is SUPERSEDED by the simulator-forward-generation framing: validity = faithfulness vs an independent qutrit oracle + anti-toy discriminability against a finite, preregistered Markov/DEM null family; decoder/LER = downstream use. This paper supports concrete leakage transport/removal physics, not a universal non-forgeability theorem or closure of process-level quantum memory. See `docs/twin_validation/notion123_taxonomy_literature_closure_2026-07-13.md`.

---

## 1. Metadata

- **Authors.** Kevin C. Miao* and Matt McEwen* (equal lead), Juan Atalaya, Dvir Kafri,
  Leonid P. Pryadko, … (full Google Quantum AI author list — the standard ~100-author
  Sycamore roster), with theory/simulation leads J. Atalaya (models/analysis), D. Kafri &
  L. Pryadko (simulation tools), and A. N. Korotkov, D. Sank, Yu Chen (guidance). Google
  Quantum AI, Santa Barbara / Venice CA, + UCSB, UMass Amherst, Auburn, UC Riverside.
- **Venue / status.** arXiv preprint Nov 2022; published Nature 2023. An **experimental
  hardware paper** on a real Sycamore processor, *not* a decoder or simulation paper.
- **Object.** Characterize how **leakage** (population escaping the computational
  `{|0⟩,|1⟩}` subspace into `|2⟩`, `|3⟩`, …) **builds up over QEC cycles and spreads through
  multi-qubit gates into space-time–correlated errors**, then **remove it from *every* qubit
  every cycle** via a new **Data-Qubit Leakage Removal (DQLR)** operation, and show this
  restores the QEC assumption of (near-)independent errors.
- **Headline numbers.** (i) ~**10×** reduction in steady-state data-qubit leakage
  population vs the best prior partial-removal; device-wide average leakage **< 1×10⁻³**;
  (ii) DQLR holds data-qubit leakage at **~1×10⁻³** and measure-qubit at **<1×10⁻⁴** *flat*
  across 30 cycles (No-reset rises to ~5% data / ~3% measure); (iii) under DQLR, injected
  **leakage perturbs logical error like injected Pauli error** (decomposed weight driven to
  ≈1), i.e. leakage stops being a correlated, super-weight error; (iv) the d=3 surface-code
  weight-4 **detection probability stabilizes at ~18%** instead of climbing.
- **Why it is in our library.** This is **Google's at-scale leakage model and rates,
  measured on the same Sycamore family that produced our R2 datasets**. It supplies the
  physical leakage mechanism, the per-cycle/steady-state rates, the gate-level transport and
  phase numbers, and the **detector-/correlation-level fingerprint** (rising detection
  probability + non-local `pij` time correlations) — the **empirical spec the simulator's
  leakage SOURCE must reproduce faithfully** when it forward-generates the record `{det,obs}`.
  After the latent leakage state is hidden, its persistence and transport produce a
  **multi-round, space-time-correlated notion-2 record** in the measured protocol. Its
  faithfulness is scored against an INDEPENDENT qutrit-DM oracle. Whether a registered finite
  Markov/DEM null family can reproduce the chosen record statistics is a separate project
  experiment, not a theorem or process-level quantum-memory classification supplied here.

**One-sentence takeaway.** Leakage is a long-lived (`T1` of `|2⟩` ≳ 10 cycles), gate-mobile,
high-decomposed-weight error that *accumulates and correlates in space-time*; on this device and
for the reported observables, DQLR strongly contains it and brings selected logical/correlation
metrics closer to the paper's Pauli-model predictions. The paper does not prove full-record
equivalence to a Pauli/DEM model.

---

## 2. TL;DR

Leakage breaks the founding assumption of QEC (errors uncorrelated in space and time) in
three compounding ways, all measured here on hardware:

1. **It is long-lived.** An injected `|2⟩` on a data qubit decays with a constant of **~4.4
   surface-code cycles** (each cycle ≈ 1 µs), *faster* than bare `T1` of `|2⟩` (which alone
   can exceed 10 cycles) only because gates actively transport/de-excite it (Fig. 1c).
2. **It is mobile.** The diabatic CZ gate puts higher levels on resonance, so a leaked qubit
   *transports* its leakage to neighbours: `|30⟩↔|12⟩` moves ~**18–19%** of the population
   and `|31⟩↔|22⟩` moves ~**58–61%** per gate (Fig. 2b, Fig. S1c). Even without transport, a
   `|2⟩` neighbour imprints a **spurious ~0.65π phase** on the non-leaked qubit through the
   CZ (Fig. 2e) — a direct computational error.
3. **It accumulates and correlates.** Operations generate **~5×10⁻³ leakage population per
   cycle**; with No-reset this saturates to ~5% (data) / ~3% (measure) and never stabilizes,
   driving a *rising* detection probability and *non-local* (`|t−t'|>1`) `pij` time
   correlations >1% (Figs. 3a, 5a, S7) — the experimental signature that the iid assumption
   has failed.

**DQLR** (multi-level reset on measure qubits + a `LeakageISWAP` that shuttles data-qubit
`|2⟩` onto the measure qubit, then resets it) removes leakage from *every* qubit *every*
cycle. Result: leakage held at ~10⁻³ flat over 30 cycles, detection probability flat at
~18% (w4) / ~11% (w2), non-local `pij` correlations crushed to ~0.1–0.2%, and **injected
leakage degrades the logical error rate with the same near-linear dependence as injected
Pauli error** — including the projected `Λ₅/Λ₇` error-budget at d=5/7 (simulation), where
DQLR keeps `1/Λ_{5/7}` *linear* in leakage (`≈ 111·P_L + 0.2`, R²=0.983) while MLR blows up
nonlinearly. Net: the reported experiment and simulation support DQLR as a promising route to
keeping leakage compatible with scaling in the tested regime; they do not establish that every
post-DQLR observable is faithfully predicted by a Pauli simulation.

For our program: this paper is the **canonical, hardware-anchored leakage spec** — model,
rates, transport matrix, phase error, and the **detector-level effects** (rising detection
probability + non-local time correlations) the **simulator's leakage source must reproduce
for FAITHFUL forward generation** of the record `{det,obs}`. These effects show multi-round
record memory after the latent leakage state is hidden. Whether they distinguish the source
from a finite, preregistered Markov-`k`/DEM null family remains a project-level empirical test;
the paper neither proves universal DEM irreducibility nor closes notion-3. Faithfulness against
the exact qutrit-DM oracle remains separate, and decoder/LER is downstream product use.

---

## 3. Main contribution + core method (in full detail)

### 3.1 The leakage problem, made quantitative (Section 1, "Characterizing the spread")

Transmons are weakly nonlinear: levels are closely spaced, so drives that act on `|0⟩↔|1⟩`
leak into `|2⟩`, `|3⟩` from single-qubit gates [18,19], entangling gates [20–24], and
measurement [25,26] (p. 1, ¶1–3). Leakage is uniquely dangerous for QEC because a leaked
qubit (a) is **long-lived** and (b) **induces errors on neighbours, even leaking them**,
i.e. it is a **high-decomposed-weight** event: the number of independent Pauli errors needed
to mimic one leakage event is large [27], precisely the regime MWPM-style decoders handle
worst (p. 2–3).

**Leakage lifetime & transport (Fig. 1c, p. 2).** Inject a full `|1⟩→|2⟩` rotation on the
central data qubit of a d=3 surface code (near-50% `|2⟩`), then run the code and resolve
`|2⟩` at the end of each truncated cycle:
- Decay constant **~4.4 cycles** (cycle ≈ 1 µs), *somewhat faster* than bare `T1(|2⟩)`
  because gate interactions help de-excite — but `T1(|2⟩)` alone can exceed **10 cycles**.
- **Spatial spread:** the inset shows the injected population does *not* stay put — it is
  transported to neighbours as the circuit runs; at d=3 it reaches *every* qubit in the code
  (17 qubits, Fig. S4).

**Excess leakage population** is the operational observable throughout:
`excess = (population with injection) − (population without injection)` (Fig. 1c caption),
which isolates injected dynamics from intrinsic heating.

**Leakage transport through the diabatic CZ (Fig. 2, Section 1; SI S1).** The Sycamore CZ
is a *diabatic* gate [14,17,31]: qubits are biased so `|11⟩↔|20⟩` is on resonance and tuned
to a 2π rotation there (the intended CZ). The same bias aligns **higher-level resonances**
(Fig. 2a eigenenergy ladder, detuning by the common nonlinearity `η`):
- `|31⟩↔|22⟩` (direct): `|3⟩` on the high qubit drives the low qubit to `|2⟩` while the high
  qubit stays in `|2⟩`.
- `|30⟩↔|12⟩` (two-photon, mediated by `|21⟩` detuned by ~`η`): lets `|2⟩` on the low qubit
  move to `|3⟩` on the high qubit.

These **leakage-transport processes are what let leakage spread, even within a single
cycle** (p. 3). Measured **relative population transport `P_t`** (net change in state
populations) for a calibrated CZ (Fig. 2b, Fig. S1c):
- `|30⟩↔|12⟩`: ~**18–19%** (`+19%/−18%`),
- `|31⟩↔|22⟩`: ~**58–61%** (`+61%/−60%`),
- plus first hints of higher resonances (`|42⟩↔|33⟩`).
SI S1 gives the effective-coupling derivation for the two-photon process. With `g` the
induced `|11⟩–|20⟩` coupling:

```
g_{|30⟩–|21⟩} = √3 · g,
g_{|21⟩–|12⟩} = 2 · g,
g_eff = g_{|30⟩–|12⟩} = − g_{|21⟩–|12⟩} · g_{|30⟩–|21⟩} / η,
P_t(|30⟩↔|12⟩) = sin²(g_eff · t).            (SI S1, p. 11)
```

**Leakage phase error (Fig. 2d–e, Fig. S2).** Even when transport is forbidden (high qubit
in `|2⟩`, low qubit computational), the CZ imprints a **spurious phase** on the non-leaked
qubit. A modified Ramsey with an interleaved CZ to a neighbour prepared in `|0⟩`/`|1⟩`/`|2⟩`
gives phase shifts `φ=0` (`|0⟩`) and `φ=π` (`|1⟩`) as expected, but **`φ ≈ 0.65π` when the
neighbour is in `|2⟩`** (Fig. 2e, ECDF over 20 qubit pairs). This is a *direct, detectable
computational error* generated by a leaked neighbour. (Conclusion, p. 3: each CZ a leaked
qubit sees has significant probability to add a computational error, move the leakage, or
*induce new leakage*.)

> **Modelling takeaway:** the per-gate non-Pauli action of leakage has two measured channels
> — **population transport** (a classical, level-mixing stochastic map with the `P_t` above)
> and a **coherent phase** (~0.65π conditional on a `|2⟩` neighbour). Both are *conditional
> on a neighbour's leakage state*, which is exactly what makes leakage **spatially
> correlated** and non-Pauli.

### 3.2 Suppressing leakage during the circuit — three strategies (Section 2)

Three families of leakage-removal exist (p. 4): **swap-type** [27,37] (periodically exchange
data/measure roles so all qubits get reset — but only half are reset each cycle, so leakage
still moves), **feedback-type** [29,30] (detect leakage from measurement patterns and feed
back — but conditional, so leakage causes errors before it is noticed), and **direct-type**
[38] (remove leakage without disturbing the computational state). Given transport, the
authors argue swap- and feedback-type are insufficient and pursue **direct** removal.

The three compared strategies:

1. **No Reset.** No end-of-cycle operation; best case for a naive Pauli model, worst case
   for leakage. Requires redefining detectors to compare *time-next-neighbour*
   measurements on the same measure qubit (since the qubit is left in the measured state, not
   `|0⟩`) [10] — negligible effect on performance (SI S2).
2. **MLR (Multi-Level Reset).** A multi-level reset gate [35] on **measure qubits** at the
   end of every cycle (gate time 160 ns here). Removes measure-qubit leakage but **leaves
   data-qubit leakage untouched**; adds idle error to data qubits during the reset.
3. **DQLR (Data-Qubit Leakage Removal) — the new operation.** First do MLR on all measure
   qubits; then a **`LeakageISWAP`** gate between each measure–data pair that performs an
   ISWAP in the `|11⟩–|20⟩` subspace, shuttling data-qubit `|2⟩` onto the (already reset)
   measure qubit; then a **second reset** of the measure qubits (SI S2). Key property: when
   the measure qubit is correctly in `|0⟩`, `LeakageISWAP` **removes `|2⟩` from the data
   qubit**; a residual `|1⟩` on the measure qubit (reset error) would be converted to
   data-qubit leakage, but this path is measured to be rare enough not to raise data-qubit
   leakage. **DQLR removes leakage from *every* qubit *every* cycle** — the paper's core
   operation.

**Cost of DQLR (Fig. S3, XEB).** Cross-entropy benchmarking on the 9 data/measure pairs of
the d=3 patch: DQLR adds **< 2.5×10⁻³ error per cycle** vs idling for the equivalent
duration — low enough to insert into a sensitive surface-code circuit. (Caveat: XEB captures
leakage as an incoherent error, so DQLR's leakage-removal may *under*-report its own XEB
error relative to Idle, which lets leakage accumulate — SI S2.)

### 3.3 Effect on logical performance — the two codes (Section 3)

Two codes chosen for complementary reasons (p. 5): a **distance-21 bit-flip code** (a 1D
repetition code, classical, *well below threshold* → very low LER → fine resolution on small
leakage effects, and you can inject pure-`X`/`Z` "Pauli population" for a clean comparison),
and a **distance-3 surface code** (near threshold, sensitive to both bit- and phase-flip →
stresses calibration and exposes adverse reset effects).

**Injection calibration (Fig. 4b, p. 5).** Leakage injected by a `|1⟩→|2⟩` rotation on each
qubit after the first Hadamard layer; rotation angle to reach leakage population `P_L`:

```
θ_L = 2 · sin⁻¹ √(2 P_L).                     (p. 5)
```

Pauli "population" `P_P` injected by `X`/`Z` rotations on data/measure qubits:

```
θ_P = 2 · sin⁻¹ √(P_P).                        (p. 5)
```

The **factor-2 difference** (`2P_L` vs `P_P`) accounts for leakage injection acting only on
the `|1⟩` part of the state, whereas a Pauli rotation always affects the computational state
— a small but load-bearing modelling subtlety.

**Phenomenological fits (SI S5).** Logical error per cycle `ε` ↔ logical error probability
`p_L` after `n` cycles:

```
ε = ½ [1 − (1 − 2 p_L)^{1/n}],   p_L = ½ [1 − (1 − 2ε)^n].   (S1, S2)
```

`ε(P)` vs injected population `P` modelled as an **offset power law** `ε(P) = a (P + P₀)^b`
(S3; `P₀` is *not* claimed physical). The bit-flip-in-time data use a **Gompertz** model
`ε(n) = a·exp(−b·exp(−cn))` (S5) to capture the transient rise then saturation.

---

## 4. Key results (figures and tables)

### 4.1 Leakage dynamics during the code (Fig. 3, Fig. S4)

**Fig. 3a — steady-state leakage, 30 cycles, d=3 surface code** (truncate-and-resolve-`|2⟩`):
| Strategy | Data-qubit avg leakage | Measure-qubit avg leakage | Stable over 30 cycles? |
|---|---|---|---|
| **No Reset** | rises to ~**5%** (still growing) | rises to ~**3%** | **No** |
| **MLR** | rises to **>1.5%** | ~**3×10⁻⁴** | data: no |
| **DQLR** | ~**1×10⁻³** | **<1×10⁻⁴** | **Yes (flat)** |

**Fig. 3c — within-cycle moment-resolved leakage (cycles 25–30, stabilized).** MLR: data
qubits saturate ~1.5% (consistent with 3a), measure qubits start each cycle ~2×10⁻⁴, grow as
operations leak, then are reset back. DQLR: both grow over the cycle, data qubits start
each cycle at ~1×10⁻³, rise to ~5×10⁻³ right after measurement, then are removed. **Estimated
leakage generated per cycle ≈ 5×10⁻³** (the per-cycle leakage *source* rate). Fig. S4 shows
the same as a spatial movie over 5 cycles: No-reset spreads to nearly all 17 qubits; DQLR
brings all qubits to ~10⁻³ within **2 cycles**.

### 4.2 Bit-flip code: leakage ≈ Pauli under DQLR (Fig. 4, Fig. S5)

**Fig. 4a — d=21 bit-flip code, 60 cycles, logical error vs injected population:**
- **No Reset:** even **< 1% injected leakage** drives logical error **> 40%**, whereas
  correctable **Pauli** error tolerates ~**5%** population before similar logical error.
  (Leakage is ~5× more damaging per unit population, the decomposed-weight effect.)
- **MLR:** much lower baseline, but logical error still rises **far faster for leakage than
  Pauli**.
- **DQLR:** the leakage and Pauli curves nearly **coincide** → the **decomposed weight of a
  leakage event is driven to ≈1**; leakage now behaves like an equivalent amount of Pauli
  error. Experiment–simulation agreement is good (slight *under*-estimate of leakage-induced
  error remains, attributed to within-cycle leakage dynamics not fully captured).

**Fig. S5 — bit-flip logical error in time (60 cycles):** No-reset > 1×10⁻² by ~25 cycles;
MLR (no injection) reaches ~1×10⁻² by 30 cycles; **DQLR sustains < 5×10⁻³ over 60 cycles**
(~1×10⁻³ at 60 with no injection) — a clear time-scaling advantage.

### 4.3 Surface code: stabilized detection + Pauli-like scaling (Fig. 5, Fig. S6)

**Fig. 5a — d=3 surface-code average weight-4 detection probability over cycles:**
- No Reset: **rises continuously** (leakage buildup → more detections).
- MLR: most of the rise mitigated but **still +2.5% over the first 15 cycles**.
- **DQLR: immediately stabilizes at ~18% and stays flat** for the whole run. (Fig. S6: the
  weight-2 stabilizers behave analogously; DQLR holds them flat at **~11%**.) This directly
  resolves the *rising detection probability* seen in SOTA QEC [15–17] even with partial
  removal/post-selection.

**Fig. 5b — d=3 logical error at 15 cycles vs injected leakage:** ordering
No-Reset > MLR > DQLR (DQLR lowest), and No-Reset/MLR degrade faster with injected leakage
than DQLR — DQLR suppresses the correlated component despite its extra cycle time/errors.

**Fig. 5c — projected d=5/d=7 scaling (SIMULATION, SI S6).** Define the exponential
suppression factor `Λ_{5/7} = ε₅/ε₇` and the **error budget `1/Λ_{5/7}`** (inverse
suppression between d=5 and d=7). With **zero leakage**, `Λ_{5/7} ≈ 7.2` regardless of
strategy. Injecting up to **4×10⁻³ leakage/round** (comparable to intrinsic device rates):
- **MLR:** `1/Λ_{5/7}` rises **rapidly and nonlinearly** (leakage kills exponential scaling).
- **DQLR:** `1/Λ_{5/7}` rises **slowly and near-linearly** — fit `1/Λ_{5/7} ≈ 111·P_L + 0.2`,
  **R² = 0.983** — the linear-in-rate signature of an **uncorrelated** error source.

### 4.4 The correlated-error fingerprint: `pij` matrices (SI S7, Fig. S7) — *most relevant to us*

`pij` correlation matrices [14,17,35,39] estimate the probability of an error-graph edge
between detection nodes `i=(s,t)`, `j=(s',t')` (stabilizer + time coordinates). The paper
forms **time autocorrelation** matrices by averaging over same-stabilizer pairs:

```
p̄_{t,t'} = ⟨ pij ⟩ over { i,j : s = s' }.     (S6)
```

and a nearest-neighbour-in-space version `p̄_{t,t'} = ⟨pij⟩ over {s−s'=1}` (S7).

**The physical reading (Fig. S7, p. 16–17):** in the paper's independent, local Pauli
reference, elementary errors produce detections on **consecutive** cycles, so
`p̄_{t,t'} ≠ 0` is concentrated at `|t−t'| = 1`. Non-local (`|t−t'| > 1`) correlations are
therefore evidence against that specific iid reference and are consistent with the measured
leakage/crosstalk mechanisms; they are not a unique identifier of leakage among all possible
correlated latent-state or DEM models.
- **No Reset:** non-local correlations appear at cycle 1 and **intensify over 30 cycles**,
  staying **> 1%** at large `|t−t'|` — leakage-induced correlations dominate and QEC cannot
  scale in time.
- **MLR:** non-local correlations **reduced** but persistent — **~1% at distance-2**, decays
  slowly, **still > 0.1% even at distance-10**; residual is **data-qubit leakage** (incl. the
  CZ phase shifts of Fig. 2e).
- **DQLR:** non-local correlations **crushed to ~0.2% at distance-2** and **< 0.1% beyond** —
  approaching the iid ideal; DQLR also does **not** introduce new correlations.
The same hierarchy (No-Reset > MLR > DQLR) holds for the nearest-neighbour-in-space
`s−s'=1` correlations (long-diagonal edges).

### 4.5 The hypothetical-device simulation error model (Table S1) — *directly reusable*

The d=5/d=7 below-threshold simulations (Fig. 5c) use a **Kraus-operator simulation** [17]
that **explicitly includes leakage transport, leakage phase errors, and the MLR/DQLR
parameters**, with **zero intrinsic leakage in the baseline** (leakage enters only via
injection). Baseline error model (**Table S1**, p. 15):

| Parameter | Value |
|---|---|
| Single-qubit-gate Pauli error | 2×10⁻⁴ |
| CZ-gate Pauli error | 1×10⁻³ |
| Readout and reset error | 1×10⁻² |
| Idling Pauli error from relaxation | 3×10⁻³ |
| (Idling Pauli error) from dynamical decoupling | 1×10⁻³ |
| Qubit `T₁` | 75 µs |
| Qubit `T₂` | 75 µs |
| Single-qubit-gate time | 15 ns |
| CZ-gate time | 25 ns |
| Combined readout + reset time | 300 ns |

(These are *projected/hypothetical* "lower than currently realizable" component errors, used
to probe the sub-threshold regime, not the live device's calibration.)

### 4.6 SI readout / transport details (Fig. S1, Fig. S2)

Fig. S1: a calibrated readout pulse distinguishes the four lowest levels; the measured
"With-CZ minus Baseline" population-transport matrices give the Fig. 2b numbers; T1 decay
during readout reduces diagonal populations a few percent (worse for higher levels). Fig. S2:
raw modified-Ramsey traces (sinusoidal fits) yielding the 0.65π phase, over 20 qubit pairs.

---

## 5. **USEFUL FOR OUR PROJECT** (concrete, with page/eq refs)

Our program is the **error-coupling SIMULATOR**: a faithful FORWARD GENERATOR of the record
`{det,obs}` for surface-code cycles, whose validity is (i) **FAITHFULNESS** — the generated
record bounded against an INDEPENDENT oracle (exact qutrit-DM / from-scratch / closed form) —
and (ii) **ANTI-TOY LEGITIMACY** — a project test of whether the leakage feature is
DISTINGUISHABLE from a finite, preregistered CP-divisible / Markov-`k` / Pauli-DEM null
family on fixed statistics. The paper does not report that comparison. It is the
**hardware-anchored leakage spec** the simulator's leakage source must reproduce. Mapping to
our three needs (a) canonical
leakage model + bounded simplification, (b) scalable faithful generation, (c) the faithful
OUTPUT channels the record must carry:

### 5.1 (a) Canonical leakage model + the rates the source must reproduce

The simulator must carry leakage as **its own degree of freedom** (qutrit/`|2⟩`-aware, not a
Pauli twirl), with these *measured* rates as the targets its forward-generated record must
reproduce (each bounded vs the exact qutrit-DM oracle, per `docs/FAITHFULNESS_PROTOCOL.md`):

- **Per-cycle leakage generation rate ≈ 5×10⁻³** (Fig. 3c, p. 4). This is the *source* term
  per qubit per cycle — the single most important scalar for "how much leakage exists."
- **Leakage lifetime: decay constant ~4.4 cycles** for injected `|2⟩` (Fig. 1c, p. 2);
  underlying `T₁(|2⟩) ≳ 10 cycles`. → in the simulator, `|2⟩` must **persist across multiple
  rounds** — after the leakage state is hidden, this persistence can make the generated record
  *temporally* correlated (notion-2 memory). It rejects a memoryless single-round null if the
  preregistered multi-round statistic resolves the tail; whether a richer finite-order latent
  model or correlated DEM also fits remains an empirical model-comparison question.
- **Steady-state populations to match the regime you simulate** (Fig. 3a): No-reset ~5%
  data/~3% measure (the "do-nothing" worst case); **DQLR ~1×10⁻³ data / <1×10⁻⁴ measure**
  (the "removed" best case). Intrinsic device leakage **~4×10⁻³/round** (Fig. 5c, p. 6).
- **Per-CZ leakage transport (the spatial-spread mechanism), Fig. 2b / Fig. S1c (p. 3, 11):**
  - `|30⟩↔|12⟩`: **~18–19%** population transfer,
  - `|31⟩↔|22⟩`: **~58–61%** population transfer,
  with the two-photon effective-coupling form `P_t = sin²(g_eff t)`, `g_eff = −2g · √3 g/η`
  (SI S1, p. 11). → the simulator's two-qubit gate must include a **level-mixing stochastic map
  conditioned on the neighbour's leakage state**, not just an iid on-site Pauli error. This
  neighbour conditioning produces spatial dependence, but the paper does not prove that no
  correlated DEM or latent-state construction can represent the resulting record.
- **Leakage phase error: ~0.65π coherent phase** imprinted on a computational qubit by a CZ
  to a `|2⟩` neighbour (Fig. 2e, p. 3). → a **coherent, neighbour-conditioned `Z`-rotation** —
  a per-gate non-Pauli action the source must reproduce at the channel level. Its coherent
  channel action is not equal to a Pauli channel in general; whether the chosen passive record
  statistics distinguish it from a specified Pauli/DEM null is a separate project test.

**Evidence for, but not a bound on, a Pauli simplification (our deliverable (a)).** After DQLR,
the injected-leakage and injected-Pauli curves are close for the reported Fig. 4a logical
observable, while Fig. 5c gives `1/Λ_{5/7} ≈ 111·P_L + 0.2` (R²=0.983) in the paper's projected
simulation. This supports using the DQLR regime as a **candidate low-correlation control** on
those observables; it does not prove equality of full record laws or fidelity of every
Pauli/DEM approximation. Conversely, No-reset / partial-removal data show stronger non-Pauli
channel physics and longer-range record correlations (Figs. 4a, S7), but do not establish
irreducibility with respect to all correlated DEMs or hidden-state Markov models. We may run
these regimes as a preregistered positive/control pair and compare a finite named null family,
but whether discriminability vanishes under DQLR is an empirical project outcome, not something
the paper proves. The paper also reports that its simulation **slightly under-estimates**
leakage-induced error (p. 6), confirming that within-cycle leakage dynamics remain imperfectly
captured; this is a caveat to bound independently under `docs/FAITHFULNESS_PROTOCOL.md`, not an
error bound supplied by the paper.

### 5.2 (b) How to faithfully generate leakage at scale

- **Use a Kraus-operator simulation with explicit `|2⟩` (and ideally `|3⟩`) levels** that
  includes (i) leakage transport, (ii) leakage phase errors, (iii) the removal operation —
  this is exactly the method the paper used for d=5/d=7 (SI S6, p. 14; method ref [17]).
  Their baseline carries **zero intrinsic leakage** and injects leakage as a controlled knob
  (`θ_L = 2 sin⁻¹√(2P_L)`, p. 5) — a **clean forward-generator design pattern**: a tunable
  leakage-rate dial on top of a Pauli baseline, with a `0%`-injection control. We can register
  that endpoint as one control in a finite-null comparison, but the paper does not perform or
  certify our anti-toy test. The generated record on this qutrit path is what gets bounded
  independently against the exact qutrit-DM oracle for faithfulness.
- **Adopt Table S1 (p. 15) verbatim as a starting baseline error model** for the Pauli
  substrate (1q 2×10⁻⁴, CZ 1×10⁻³, readout+reset 1×10⁻², idle-relax 3×10⁻³, DD-idle 1×10⁻³,
  `T₁=T₂=75 µs`, gate times 15/25 ns, RO+reset 300 ns). Under **baseline discipline** these
  are *Google's published constants* — declare the source (this paper, Table S1) alongside
  any numbers.
- **The injection circuit is a `|1⟩→|2⟩` rotation after the first Hadamard layer** (Fig. 4b /
  Fig. 5b inset) — a concrete, reproducible insertion point for a leakage knob in a
  surface-code circuit.
- **Scale validation target:** at d=3 leakage reaches all 17 qubits (Fig. S4); the spatial
  spread is *local-per-gate but global-over-cycles*, so a scalable simulator only needs the
  **per-gate transport map + multi-round persistence**, and the global correlation of the
  generated record emerges — no need for a hand-coded long-range kernel.

### 5.3 (c) The faithful OUTPUT channels the generated record must carry

Leakage's value to us is its measured **detector-level structure**. The simulator must reproduce
these signatures in the record `{det,obs}` it forward-generates (faithfulness bounded vs the
qutrit oracle), and expose the additional non-Pauli output channels below. A finite,
preregistered null comparison then asks how much of that structure simpler named models can
reproduce; the answer is not supplied by this paper. Whether a *downstream* decoder can exploit
the structure is product use, not validity:

1. **Rising / elevated detection probability** (Fig. 5a, S6): weight-4 detection climbs under
   No-reset and sits at ~18% under DQLR; weight-2 at ~11%. A leakage-aware simulator should
   reproduce the **time-dependence** of detection probability. A stationary iid Pauli reference
   is flat by construction, so the rise rejects that reference; nonstationary or latent-state
   nulls are not excluded by the paper.
2. **Non-local time correlations `p̄_{t,t'}` at `|t−t'| > 1`** (SI S7, Fig. S7; eqs. S6–S7,
   p. 16). This is a clean **notion-2 record observable**: with the paper's iid local-Pauli
   reference, `p̄_{t,t'}=0` for `|t−t'|>1` by construction; the leakage regimes show it nonzero
   (No-reset >1% out to large distance; MLR ~1% @ dist-2, >0.1% @ dist-10; DQLR ~0.2% @
   dist-2). The multi-round statistic is therefore a good preregistered discriminator against
   that narrow reference. A finite-order hidden-state model or a correlated DEM with long-range
   edges may also express such pairwise structure, so representability and distinguishability
   must be tested on fixed full-record statistics. Our differentiable-DEM / hypergraph route
   (`hypergraph_dem`) can emit long-range time hyperedges, but that project capability is not a
   result of this paper.
3. **A leakage-flag / soft channel.** The paper *resolves `|2⟩` directly* by truncate-and-
   measure (Figs. 1c, 3) — i.e. leakage **is measurable** as a third outcome. For our SOFT
   READOUT axis this motivates a simulator whose **measurement emits more than a hard bit**: a
   `|2⟩`-population (or analog-IQ proxy) leakage indicator. This is an **additional faithful
   OUTPUT channel** the record carries (`soft_readout.py`), not part of the validity chain; a
   1-bit "leakage detected" side-channel (cf. leakage-detection refs [29]) is likewise a
   non-Pauli output the generated record can expose.
4. **Space-correlated, neighbour-conditioned errors** (the CZ phase ~0.65π and transport):
   detections come in **spatially adjacent clusters tied to a leaked qubit's footprint** — the
   simulator must make the error *conditional on a latent per-qubit leakage state*. This creates
   spatial dependence and rejects an iid on-site model, but does not by itself prove that no
   correlated DEM can reproduce the selected passive-record statistics.

**Net framing for us.** This paper supplies measured **physics + rates + detector fingerprints**
for leakage with multi-round notion-2 structure. Our contribution is *not* to re-derive leakage
removal, but to build a simulator whose leakage-bearing record is faithful to an independent
qutrit-DM oracle and then test it against a **finite, preregistered** Markov-`k`/DEM null family
on fixed statistics such as the detection rise and non-local `p̄_{t,t'}`. DQLR-style removal is
a useful low-leakage control; neither full-record Pauli equivalence nor vanishing project
discriminability follows from Fig. 4a alone. LER is downstream product use
(`docs/METRICS.md`), not a validity criterion.

---

## 6. Limitations / what does NOT apply

- **It is a removal paper, not a forward-generator.** The contribution is the **DQLR
  operation** + characterization; there is **no decoder, no learned model, no soft-information
  decoding** here. We borrow the *forward physics* — the leakage model, rates, and detector
  fingerprint the simulator's source must reproduce — not any inference method. The closeness
  of selected injected-leakage and injected-Pauli observables after DQLR motivates a
  low-leakage control, but it is not a full-record equivalence theorem and does not show that a
  matched Markov/DEM law coincides with the generated record. The strongest measured notion-2
  signal occurs in the **un-removed** regime; we can compare it with DQLR under a registered
  finite-null protocol, with the outcome left open.
- **No record-level or decoder benchmarks to reuse.** Logical performance is reported as raw
  logical error probability / detection probability / `Λ` — there is **no MWPM-vs-X comparison**,
  no per-leaf numbers. That is fine: LER/decoder numbers are downstream product, not our
  validity chain. What we take is the *record-level* fingerprint (detection probability,
  `p̄_{t,t'}`), which we must generate from our own simulator and score against the qutrit-DM
  oracle + a matched null; the paper supplies the targets, not the scored artifact.
- **d=5/d=7 results are simulation, not hardware** (Fig. 5c, SI S6). The on-hardware codes
  are only **d=3 surface** and **d=21 bit-flip**. The `Λ_{5/7} ≈ 7.2` and `1/Λ ≈ 111 P_L+0.2`
  numbers are from the **Table S1 hypothetical device**, *not* a measured large surface code.
  Treat them as **prediction-band**, not measured fact, in our epistemic-status ledger.
- **Hardware-specific transport numbers.** The `P_t` transport (18%/61%) and the 0.65π phase
  are **Sycamore diabatic-CZ specific** (p. 3) — they depend on the gate type, length, and
  effective inter-level coupling, "not normally calibrated." Our simulator should treat them as
  **representative parameters to sweep** (a declared, bounded simplification), not universal
  constants; a different gate set (or the iSWAP-like gates in some datasets) would have
  different leakage transport.
- **Within-cycle leakage dynamics under-captured.** The authors flag (p. 6, and SI) that even
  their leakage-aware simulation **under-estimates** leakage-induced logical error, because
  leakage motion *inside* a single cycle is hard to model — explicitly named as future work.
  Any simulator we build inherits this as a **declared, bounded simplification**
  (`docs/FAITHFULNESS_PROTOCOL.md`): matching *steady-state* and *cross-cycle* record statistics
  is achievable; perfectly matching *intra-cycle* leakage is not, on this paper's own evidence.
- **No `|3⟩+` quantitative budget.** The model is dominated by `|2⟩`; `|3⟩` enters via the
  transport resonances (`|30⟩`, `|31⟩`) and there are hints of `|42⟩↔|33⟩`, but the paper
  does not give a full higher-level population budget. A faithful simulator may need `|3⟩` for
  the two-photon transport channel, but quantitative `|3⟩`/`|4⟩` rates are not tabulated here.
- **`P₀` and fit offsets are non-physical** (SI S5): the offset power law's `P₀` is explicitly
  *not* an intrinsic-error claim — do not lift fit constants as physical rates. The reusable
  physical scalars are the directly-measured ones (§5.1), not the curve-fit parameters.

---

## 7. Key equations / numbers cheat-sheet

| Ref | Item | Value / form |
|---|---|---|
| Fig. 1c (p. 2) | Injected-`|2⟩` decay constant | **~4.4 cycles** (cycle ≈ 1 µs); `T₁(|2⟩) ≳ 10 cycles` |
| Fig. 2b / S1c (p. 3, 11) | CZ leakage transport `|30⟩↔|12⟩` | **~18–19%** |
| Fig. 2b / S1c | CZ leakage transport `|31⟩↔|22⟩` | **~58–61%** |
| SI S1 (p. 11) | Two-photon transport coupling | `g_eff = −2√3 g²/η`, `P_t = sin²(g_eff t)` |
| Fig. 2e (p. 3) | Spurious CZ phase from `|2⟩` neighbour | **φ ≈ 0.65π** (vs 0 for `|0⟩`, π for `|1⟩`) |
| Fig. 3c (p. 4) | Leakage generated per cycle | **~5×10⁻³** |
| Fig. 3a (p. 4) | Steady-state leakage: No-reset / MLR / DQLR (data) | ~5% / >1.5% / **~1×10⁻³** |
| Fig. 3a | Steady-state leakage (measure) | ~3% / ~3×10⁻⁴ / **<1×10⁻⁴** |
| p. 5 | Leakage injection angle | `θ_L = 2 sin⁻¹√(2 P_L)` |
| p. 5 | Pauli injection angle | `θ_P = 2 sin⁻¹√(P_P)` |
| Fig. 4a (p. 5–6) | No-reset: <1% leakage → logical error | **>40%** (vs ~5% Pauli population for similar) |
| Fig. 5a (p. 6) | DQLR weight-4 detection prob (stable) | **~18%** (weight-2 ~11%, Fig. S6) |
| Fig. 5c (p. 6) | Zero-leakage suppression factor (d5/d7 sim) | `Λ_{5/7} ≈ 7.2` |
| Fig. 5c / SI S6 | DQLR error-budget linearity | `1/Λ_{5/7} ≈ 111·P_L + 0.2`, R² = 0.983 |
| SI S2 / Fig. S3 | DQLR added error per cycle (XEB) | **< 2.5×10⁻³** |
| SI S7 (p. 16) | Non-local time-corr at `|t−t'|>1`: No-reset / MLR / DQLR | >1% / ~1%@d2 (>0.1%@d10) / **~0.2%@d2 (<0.1% beyond)** |
| Eqs. S6–S7 (p. 16) | Time-/space-autocorrelation `p̄_{t,t'}` | avg of `pij` over same-`s` / `s−s'=1` |
| Eqs. S1–S2 (p. 14) | `ε ↔ p_L` over `n` cycles | `ε = ½[1−(1−2p_L)^{1/n}]` |
| Table S1 (p. 15) | Sim baseline (1q/CZ/RO+reset/idle Pauli; T₁=T₂; times) | 2e-4 / 1e-3 / 1e-2 / 3e-3,1e-3; 75 µs; 15/25/300 ns |

---

## 8. How to use / trust

- **Cite for:** the **canonical hardware leakage model and rates** (per-cycle generation
  ~5×10⁻³, lifetime ~4.4 cycles, transport 18%/61%, phase 0.65π); the **detector-level
  leakage fingerprint** (rising detection probability + non-local `pij` time correlations);
  the **DQLR removal operation**; the **leakage-aware Kraus simulation recipe + Table S1
  baseline**; and the observed closeness of selected leakage- and Pauli-injection observables
  after removal. Do not cite that closeness as a full-record equivalence or a general bound on
  when a Pauli approximation is valid.
- **Do not cite for:** any **decoder** result, any **soft-information / learned-decoder**
  method (none here); large-distance *measured* surface-code numbers (d=5/d=7 are simulation);
  universal transport constants (Sycamore-CZ specific); intra-cycle leakage as a solved
  modelling problem (authors flag it open).
- **Open questions it sets up for us:** (i) build the qutrit/Kraus **leakage source** to
  Table S1 + the §5.1 rates, run it **without** DQLR, and confirm the forward-generated record
  reproduces the **non-local `p̄_{t,t'}>1`** and **detection-rise** signatures **within a bound
  vs the exact qutrit-DM oracle** (the FAITHFULNESS target); (ii) show that record is
  **discriminable from a finite, preregistered Markov-`k`/Pauli-DEM null family** on those same
  record-level observables (the ANTI-TOY legitimacy target — measured on the record, no decoder
  in the chain); (iii) use **DQLR-equivalent full removal** (Fig. 4a collapse) as a low-leakage
  control and report whether discriminability decreases, persists, or changes observable — a
  positive/control comparison whose outcome is not fixed by the paper. Decoder %ΔLER, if
  computed, is downstream product use of the validated record (`docs/METRICS.md`), not a
  validity criterion.
