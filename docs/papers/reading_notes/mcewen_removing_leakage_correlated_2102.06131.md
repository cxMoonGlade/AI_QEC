# Full-text note — McEwen et al., *Removing leakage-induced correlated errors in superconducting quantum error correction*

> Provenance: full-text read from the local PDF
> `docs/papers/mcewen_removing_leakage_correlated_2102.06131.pdf`
> (owner-password-only encryption stripped with `pikepdf`, empty password; pages
> rendered for figure inspection with PyMuPDF). All 12 pages (6 main text + 6
> supplement) were read, including every figure (Fig. 1–6, S1–S5) and Table S1.
> arXiv:2102.06131 [quant-ph]. Published as **Nature Communications 12, 1761
> (2021)**, "Removing leakage-induced correlated errors in superconducting quantum
> error correction." Manuscript dated 29 September 2020.

---

## 1. Metadata

- **Authors.** M. McEwen, D. Kafri, Z. Chen, J. Atalaya, K. J. Satzinger, C.
  Quintana, P. V. Klimov, D. Sank, C. Gidney, A. G. Fowler, … V. N. Smelyanskiy,
  John M. Martinis, H. Neven, J. Kelly, A. N. Korotkov, A. G. Petukhov, and R.
  Barends. Affiliations: UC Santa Barbara; Google (Santa Barbara & Venice);
  Johannes Kepler University Linz; UT Dallas; UC Riverside. (The author block is
  the Google AI Quantum / Sycamore team.)
- **Venue / status.** Nature Communications (2021); arXiv:2102.06131. Experimental
  hardware paper on a **Sycamore** superconducting processor.
- **Object.** A hardware-level **multi-level reset gate** (returns a transmon to
  |0⟩ from any of |1⟩, |2⟩, |3⟩ in ~250 ns) plus an **empirical study of how
  leakage produces space- and time-correlated errors** during a repetitive
  stabilizer code, measured *in-situ* through detection-event statistics and a
  pair-correlation (`pij`) analysis.
- **Headline results.** (i) Reset gate: >99% ground-state fidelity from |1,2,3⟩ in
  250 ns, error ≈10⁻³, robust to drift (adiabatic), using only existing
  readout-resonator hardware. (ii) Leakage builds up and **saturates** during the
  code, with measure qubits leaking more than data qubits (readout is a leakage
  source); reset gives a **40× increase** in effective |2⟩ decay rate on measure
  qubits and **2.4×** on data qubits (evidence of leakage *transport* via the CZ
  gate). (iii) Injected leakage produces a **pair of detection events plus a
  long-lived correlated tail** spanning >10 rounds; reset removes the tail. (iv)
  Logical error suppression of the bit-flip code improves from Λ_bit = **1.98**
  (no reset) to **2.80** (with reset), and the code **stabilizes in ~10 rounds**
  instead of ~30.
- **Lineage.** Builds directly on the Google bit-flip / repetition-code line
  (Kelly et al., Nature 519, 66 (2015), ref [5]; "State preservation by repetitive
  error detection") and the Sycamore platform (Arute et al., Nature 574, 505
  (2019), ref [29]). Leakage-measurement methodology from Chen et al., PRL 116,
  020501 (2016), ref [15]. Reset-protocol predecessors refs [22–27] (Reed, Magnard,
  Bultink, Varbanov, …). The `pij` pair-correlation method is attributed to an
  "in preparation, Google AI Quantum and Collaborators" companion (this is the
  method later canonised in the surface-code papers).

**One-sentence takeaway.** This is the paper that *experimentally established the
phenomenology of leakage-induced correlated errors* in a real superconducting QEC
code — leakage is **long-lived (decays over many rounds), mobile (transports
between qubits through the two-qubit gate), and shows up as a detection-event tail
plus off-diagonal `pij` correlations** — and showed that a cheap multi-level reset
gate removes most of it, recovering the uncorrelated-error scaling that QEC needs.

---

## 2. TL;DR

Leakage to non-computational transmon levels (|2⟩, |3⟩) is the canonical
**non-Pauli, space-time-correlated** error in superconducting QEC. Unlike a
bit-flip, a leaked qubit (a) **persists for many stabilizer rounds** (it decays on
an energy-relaxation timescale, not per-round), (b) **moves between qubits** —
specifically a |2⟩ on a data qubit can hop to |3⟩ on a neighbouring measure qubit
through the CZ gate's |21⟩↔|03⟩ resonance — and (c) corrupts every parity check it
touches while it is excited, producing a **tail of correlated detection events**
and **long-range off-diagonal entries in the pair-correlation matrix `pij`**.
These correlations break the central QEC assumption (independent errors flipping
local pairs of detectors), so logical error rates stop improving with code size.

The authors introduce a **multi-level reset gate**: adiabatically swap all qubit
excitations into the readout resonator, hold while the resonator dumps photons to
the environment (rate κ), then return diabatically. It clears |1⟩, |2⟩, |3⟩ in
~250 ns at ~10⁻³ error, is robust to drift (adiabatic), needs no extra hardware or
strong microwave drives, and is applied to **measure qubits only** (after readout)
because it destroys quantum information. Applying it:
- raises the measure-qubit |2⟩ decay rate ~40× (Table S1);
- collapses the post-injection detection-event tail to baseline within one round
  (Fig. 4);
- removes `pij` correlations spanning >10 rounds (Fig. 5);
- improves logical suppression Λ_bit from 1.98 → 2.80 and stabilises it in ~10
  rounds (Fig. 6).

For **our program** this is a primary empirical reference for what the leakage
signal *looks like in syndrome data* — the structure a non-Pauli teacher must
reproduce (a decaying-tail correlated-error process with a hopping channel) and the
structure a leakage-aware decoder can exploit. It also supplies a closed-form,
calibration-free **`pij` estimator from detection-event correlations** (Eq. 1) that
is directly usable as a diagnostic and as decoder-edge weights.

---

## 3. Main contribution and core method (in full detail)

The paper has three tightly coupled contributions: (A) the reset gate and its
semi-classical error model, (B) an in-situ measurement of leakage growth/transport
during the code, and (C) the detection-event / `pij` correlation analysis that
exposes the leakage error structure. (A) is the engineering deliverable; (B) and
(C) are the physics that matter most for a leakage-noise model.

### 3.1 The multi-level reset gate (pg 1–3, Fig. 1–2)

**Three stages** (Fig. 1a): **swap → hold → return.**

1. **Swap.** Adiabatically sweep the qubit frequency to ~1 GHz *below* the readout
   resonator, sweeping it *past* the qubit–resonator level crossing, so all qubit
   excitations transfer into the resonator. A fast quasi-adiabatic pulse (Martinis–
   Geller, ref [28]) is used: the frequency changes slowly near the crossing and
   fast when far detuned. The diabatic (leakage-back) error of the swap is upper-
   bounded by a Landau–Zener transition:

   ```
   P_D^(s) ≪ exp[ −(2πg)² t_swap / Δf ] ~ 10⁻³                      (pg 2)
   ```
   with t_swap = 30 ns, Δf = 2.5 GHz the total qubit frequency change, and g ≈ 120
   MHz the qubit–resonator coupling.

2. **Hold.** Hold the qubit below the resonator while the resonator dumps its
   photons to the environment. This is **resonator photon decay**:

   ```
   exp(−κ t_hold) ~ 10⁻³,   t_hold ~ 300 ns,   κ ~ 1/(45 ns)        (pg 2)
   ```
   The qubit's own excitation number is essentially frozen during the hold
   (Purcell decay through the resonator is small). For swap lengths < 30 ns the
   adiabaticity breaks down and the system enters the hold in a superposition of
   the two adiabatic eigenstates, giving **coherent Rabi oscillations** that show
   up as **fringes** (incomplete reset) — visible in Fig. 2b.

3. **Return.** Return the qubit diabatically to its idle frequency. If a single
   photon remains, this is a Landau–Zener transition; diabaticity is limited by the
   control bandwidth. With an effective detuning velocity

   ```
   ν_r = (1/h) d/dt (E01 − E10) = Δf / t_r,   t_r = 2 ns            (pg 2)
   P_D^(r) = exp[ −(2πg)² / ν_r ] ≈ 0.6                             (pg 2)
   ```
   (here a *high* diabatic probability is desired — we *want* the photon to stay in
   the resonator and not come back). The multi-photon case (|2⟩, |3⟩) is handled by
   a Landau–Zener *chain* model (Sinitsyn et al., ref [31]): multiple adiabatic
   transitions move 2 or 3 photons to the resonator, which then decay rapidly.

**Two error channels of the single-excitation reset** (pg 2):
- **Dominant:** photon swaps in, *survives* the hold, and adiabatically transitions
  back during return:
  `(1 − P_D^(s)) e^(−κ t_hold) (1 − P_D^(r)) ~ 5·10⁻⁴`.
- **Sub-dominant:** failed initial swap followed by a diabatic return:
  `P_D^(s) P_D^(r) ≪ 10⁻⁴`.

**Hardware (pg 2).** Sycamore flux-tunable transmons with tunable couplers. The
demonstrated qubit: idle 6.09 GHz, nonlinearity η ≈ 200 MHz, resonator at 4.665
GHz (~1.5 GHz below the qubit at idle), g ≈ 120 MHz, resonators Purcell-filtered.
"Reset error" is defined as the probability of producing **any** state other than
|0⟩.

**Calibration / robustness (Supplement §I, Fig. S1–S2).** Five parameters:
swap/hold/return durations + two pulse-shape parameters (μ, f_swap). The pulse
angle is parametrised on the {|01⟩,|10⟩} Bloch sphere, tan θ = 2g/(f_q − f_r); the
reset must also serve |2⟩, |3⟩ which have stronger couplings and three resonance
conditions f_q = f_r, f_r + η, f_r + 2η. They replace g, f_r by free parameters
μ, f_swap. Shape coefficients λ₁ = 1.15, λ₂ = −0.2, λ₃ = 0.05 (∑λₙ = 1). They set
f_swap = f_r (a compromise across initial states) and μ = 150 MHz (larger than g =
120 MHz, which trades slightly worse |1⟩ reset for much better |2⟩/|3⟩ reset and
lower drift sensitivity). Minimum return 2 ns (filter-limited) to maximise
P_D^(r).

### 3.2 Leakage growth and transport during the code (pg 3–4, Fig. 3; Supplement §III, Table S1)

The code is the **bit-flip stabilizer code** (Fig. 1b): a 1D chain alternating data
(Q_D) and measure (Q_M) qubits; each round is Hadamards + CZ entangling gates +
measurement; **reset (R) is applied to measure qubits immediately after readout**.
Note the deliberate addition of **X gates on the data qubits each round** to
depolarise / symmetrise energy-relaxation error (this matters for the checkerboard
pattern below). They implement a **21-qubit chain** on Sycamore (Fig. 3 inset).

**Direct leakage measurement (Fig. 3).** Run the code k rounds, then terminate with
a readout that **resolves |2⟩ on every qubit**, averaging over 40 random data-qubit
initial states. The |2⟩ population **grows and saturates**. *Without reset, measure
qubits accumulate more |2⟩ than data qubits — readout is a significant leakage
source during operation.*

**Rate-equation model (Eq. S1–S2):**
```
P|2⟩(k) = p∞ (1 − e^(−Γk)) + p0 e^(−Γk)                            (S1)
Γ = γ↑ + γ↓,   p∞ = γ↑ / Γ                                        (S2)
```
γ↑ = leakage (excitation) rate per round, γ↓ = seepage (decay) rate per round.
**Table S1** (per-round rates):

| Case | qubit | γ↑ | γ↓ | p∞ |
|---|---|---|---|---|
| No reset | Data | 0.09% | 9.1% | 0.97% |
| No reset | Measure | 0.11% | 8.1% | 1.30% |
| With reset | Data | 0.11% | 22.1% | 0.50% |
| With reset | Measure | 0.11%\* | 328%\* | 0.03%\* |

(\* For measure-with-reset, reset breaks the growth pattern, so γ↓ is estimated by
fixing γ↑ to the no-reset value and using p∞ = average measure-qubit error across
rounds.) Reset gives a **~40× increase in γ↓ on measure qubits** and a **2.4×
increase on data qubits**.

**Leakage transport (pg 4).** The 2.4× data-qubit improvement — despite reset
being applied only to measure qubits — is explained as **leakage transport through
the CZ gate**. The Sycamore CZ (Foxen et al., ref [33]) needs a condition that also
places **|21⟩ and |03⟩ on resonance** (|2⟩ on the lower-frequency qubit). Where a
data qubit is *below* the measure qubit in frequency, a |2⟩ on the data qubit can
transport to |3⟩ on the measure qubit, where reset then removes it. This is the
mechanistic basis for leakage **mobility**: leakage is not pinned to the qubit it
appears on.

### 3.3 Detection-event signature of leakage — injection experiment (pg 4, Fig. 4)

To *visualise* the leakage error pattern, they **inject leakage deterministically**:
a complete |1⟩→|2⟩ rotation on a single qubit immediately after the first
Hadamards in **round 10 of a 30-round** experiment. (Because data qubits are in
|0⟩/|1⟩ and measure qubits are in an equal superposition after the Hadamard, the
injected |2⟩ population is the same on average for both.) The observable is the
**detection-event fraction** = fraction of runs in which a given stabilizer reports
an unexpected (flipped) result.

**Two distinct signatures of injected leakage** (the central qualitative result):
1. **A pair of detection events at the injection** — like a discrete bit-flip, the
   pair appears in **sequential rounds** for a measure-qubit injection, or on **both
   adjacent measure qubits** for a data-qubit injection (gray arrows in Fig. 4).
2. **A tail of correlated detection events over the lifetime of the leakage
   state** — an anomalously high detection-event level that **decays slowly over
   many rounds**. This is the time-correlated signature.

For measure-qubit injection (Fig. 4a): two adjacent peaks at detection-event
fraction **0.5** (a leaked measure qubit gives a random readout), followed by a
slowly-decaying tail. With reset, the tail **drops to baseline immediately after the
initial pair**, and the first-nine-round buildup flattens. For data-qubit injection
(Fig. 4b): a slowly-decaying increase on **both neighbouring measure qubits**; reset
makes it decay faster. They also observe small detection-event increases at qubits
3 and 6 (further from the injection at qubit 4/5) **without** reset — direct
evidence of leakage **spreading spatially**. A small **odd-even oscillation**
appears because the injected |1⟩→|2⟩ rotation does nothing when the data qubit is in
|0⟩, and the per-round X gates alternate |0⟩↔|1⟩, so energy-relaxation bit errors
are more likely in odd rounds after injection (this previews the checkerboard).

### 3.4 The `pij` pair-correlation analysis (pg 5, Eq. 1, Fig. 5; Supplement §IV)

The general (un-injected) correlation structure is quantified with the **pair
probability `pij`**: the model is that detection events arise from independent random
processes that **flip pairs of measurements** i, j, and the probability `pij` of the
process flipping measurements i and j is recovered from observed correlations:

```
              1     1     ┌      4 (⟨x_i x_j⟩ − ⟨x_i⟩⟨x_j⟩)        ┐
   p_ij  =   ─── − ───  · │ 1 − ─────────────────────────────────  │^(1/2)   (Eq. 1)
              2     2     └    1 − 2⟨x_i⟩ − 2⟨x_j⟩ + 4⟨x_i x_j⟩    ┘
```

where x_i = 1 if there is a detection event at measurement i (else 0), and ⟨·⟩ is
the average over experimental realisations. This is a **closed-form, label-free
estimator** of two-point error-process probabilities directly from detection-event
moments — exactly the quantity used to set matching-graph weights.

**What the matrices show (Fig. 5).**
- **Standard QEC assumption:** detection events occur only in *local* pairs. On the
  same measure qubit, only **adjacent-round** correlations (`p_{i,i±1}`, immediately
  off the main diagonal). On neighbouring measure qubits, only same-round or
  adjacent-round correlations (staggered CZ schedule) — entries on and just below
  the main diagonal.
- **Without reset:** large unexpected correlations appear, covering distances of
  **over 10 rounds** (long off-diagonal bands in Fig. 5b/d, left panels) — the
  leakage signature.
- **With reset:** these long-range correlations are **mostly removed** (right
  panels), recovering the expected near-diagonal structure.
- Color scale is ±1.5% correlation. Fig. 5b/c = time auto-correlations on measure
  qubit 6; Fig. 5d/e = cross-correlations between measure qubits 5 and 6.

**The checkerboard pattern (Supplement §IV, Fig. S5).** After removing leakage, an
underlying **checkerboard** in `pij` is revealed: correlations spanning an **odd**
number of rounds are larger (positive), even-round correlations are smaller and can
be **negative**. Mechanism: an energy relaxation |1⟩→|0⟩ on a data qubit flips its
two neighbouring measure qubits; the per-round X gates then alternate the data-qubit
state |0⟩→|1⟩→|0⟩→…, so the qubit can relax again only in odd-separated rounds
(it must be back in |1⟩). This produces a positive odd / negative even correlation
that decays with separation. It is more pronounced on a single measure qubit (Fig.
5c, two neighbouring data qubits contribute) than on the cross-correlation (Fig.
5e, one shared data qubit). This is an important *control* signature: it is the
expected near-diagonal correlated structure of plain energy relaxation under an
X-echo schedule, distinct from the long-range leakage tails.

### 3.5 Logical performance (pg 5–6, Fig. 6)

Detection events are fed into a **minimum-weight perfect-matching (MWPM)** decoder
(Fowler et al., ref [36]), with **matching weights set from the measured `pij`
elements**. They run 21 qubits and use **subsampling** (averaging over smaller
contiguous subsets) to extract scaling at 5, 9, 13, 17, 21 qubits, i.e.
error-correction order n = 1…5 (at least n+1 errors are needed for a logical
failure). A k-round logical-error probability P_L is converted to a per-round
logical error rate:

```
ϵ = [ 1 − (1 − 2 P_L)^(1/k) ] / 2                                   (Eq.; ref [37])
```
and in the absence of correlations ϵ should be exponentially suppressed,
```
ϵ ∝ 1 / Λ_bit^(n+1).
```

**Results (Fig. 6).**
- **Λ_bit (no reset) = 1.98; Λ_bit (with reset) = 2.80**, fitted from 9 qubits up
  (5-qubit data excluded for boundary effects degrading matching). Higher Λ is
  better (stronger per-step suppression).
- **Stability over rounds (Fig. 6b):** an *ideal* constant logical error rate gives
  a round-independent Λ. In practice, leakage buildup, data-qubit thermalisation
  and time-boundary effects inflate the apparent Λ before saturation. **No reset:**
  Λ decays over 30 rounds toward a saturation of 1.98. **With reset:** Λ stabilises
  **within ~10 rounds** to the higher value 2.80.
- Notably, reset **improves** suppression **despite adding time to the cycle**
  (more data-qubit decoherence exposure) — the gain from removing time-correlated
  leakage errors outweighs the extra idle decoherence. The paper frames error
  suppression as a property that "asymptotically emerges with space and time."

---

## 4. Key results, including figures and tables

- **Fig. 1.** (a) Reset protocol schematic (swap/hold/return; qubit populations in
  |1,2,3⟩ → resonator → environment). (b) Bit-flip code circuit with reset (R) on
  measure qubits; stars mark leakage events, red lines mark CZ paths along which
  leakage transports.
- **Fig. 2.** Reset benchmarking. (a) Qubit frequency trajectory (idle 6.09 GHz →
  past resonator 4.665 GHz → hold 1 GHz below → fast return). (b) Reset error vs
  swap time for |1⟩,|2⟩,|3⟩ (hold = 300 ns): error falls to the **readout floor
  ~0.2%** by ~30 ns swap; oscillatory **fringes** from incomplete swap, reproduced
  by theory. (c) Reset error vs hold time (swap = 30 ns): exponential decay with
  1/κ = 45 ns down to the readout floor. (d,e) Experimental and theory error
  landscapes over (swap, hold): a broad optimal region; theory floor < 10⁻³ (exp
  limited by readout). **Most reset error is in the computational basis** (which the
  code can correct).
- **Fig. 3.** |2⟩ population vs rounds (40 random initial states). Grows and
  saturates; measure qubits > data qubits without reset. Exponential fits feed Table
  S1. Inset: 21-qubit Sycamore chain layout.
- **Fig. 4.** Leakage injection (full |1⟩→|2⟩ rotation, round 10 of 30). (a)
  Measure-qubit injection: two adjacent 0.5 peaks + slowly-decaying tail; reset
  flattens and removes the tail. (b) Data-qubit injection: decaying tail on both
  neighbouring measure qubits; reset speeds the decay. Insets: detection-event
  fraction across all measure qubits (spatial spread visible at qubits 3, 6 without
  reset).
- **Fig. 5.** `pij` correlation matrices. (a) Error graph with example non-local
  space/time correlations. (b,c) Time auto-correlation on measure qubit 6 without /
  with reset. (d,e) Cross-correlation between qubits 5 and 6 without / with reset.
  Without reset: correlations span >10 rounds; with reset: long-range bands removed,
  revealing the ±1.5% checkerboard.
- **Fig. 6.** Logical code performance. (a) Logical error rate vs qubit number at 30
  rounds; exponential fit from 9 qubits gives Λ_bit = 1.98 (no reset), 2.80 (reset).
  (b) Λ_bit vs rounds: reset stabilises faster (~10 rounds) and higher; dashed line
  = bit-flip threshold (Λ = 1).
- **Fig. S1 / S2.** Reset-error landscapes vs swap frequency f_swap − f_resonator
  (S1) and vs adiabatic slope μ (S2) for inputs |1,2,3⟩. f_swap = f_r optimal for
  |1⟩ at short swaps; |2⟩,|3⟩ prefer higher f_swap and larger μ. Chosen compromise:
  f_swap = f_r, μ = 150 MHz.
- **Fig. S3.** Reset error split into **computational error (P1)** and **leakage
  error (P2 + P3)**. Computational error dominates in all cases; at the readout floor
  leakage error is ~**10× lower** than computational error. Leakage error falls
  faster with hold time (higher relaxation rate from higher states). This is a
  *desirable* property: residual reset error is mostly in-basis and correctable.
- **Fig. S4.** IQ readout scatter (I/Q demodulated) for |0⟩,|1⟩,|2⟩,|3⟩, optimised
  to distinguish the two computational states **and** to separate leakage from
  computational states (it does *not* separate |2⟩ from |3⟩). Readout floor measured
  by **heralding** (two sequential measurements, postselect |0⟩, fidelity of
  measuring |0⟩ again).
- **Fig. S5.** Odd-even / checkerboard mechanism schematic: data-qubit X gate each
  round + |1⟩→|0⟩ relaxation → detection-event pairs preferentially separated by odd
  round counts.
- **Table S1.** Per-round leakage growth/decay rates (reproduced in §3.2 above).
- **Statistics / postselection (Supplement §V).** Fig. 3: 20 random bitstrings ×
  5000 reps. Figs. 4/5/6: 40 bitstrings × 1000 reps = 40 000 realisations. For ≤10
  rounds (smaller P_L): 100 bitstrings × 10 000 reps = 1 000 000 realisations.
  **Postselection of "events":** compute logical error per time-ordered realisation,
  take a moving average over 30 realisations; total average logical error < 3% but
  during "events" the moving average can reach 50%; threshold 25% flags an event,
  ~1000 realisations removed per event, removing **~0.8% of data** total.

---

## 5. Useful for our project (concrete, with page/eq refs)

Our program: a **sim-only** teacher generates realistic-noise surface-code
**syndrome** data to train a decoder; noise must be **non-Pauli** (T1/T2, leakage
|1⟩→|2⟩ + seepage, soft IQ readout); the non-Pauli signal is decoding headroom
above Pauli decoders (MWPM/TN-MLD/RL-prior). This paper is a primary **empirical
specification of the leakage signal** that the teacher must reproduce and the
decoder must exploit.

**(a) Canonical leakage model + how to bound it.**
- **Per-round rate-equation model for leakage population** is given explicitly:
  Eq. S1–S2, `P|2⟩(k) = p∞(1 − e^(−Γk)) + p0 e^(−Γk)`, `Γ = γ↑ + γ↓`,
  `p∞ = γ↑/Γ`. This is the minimal teacher knob set: a **leakage (excitation)
  rate γ↑** and a **seepage (decay) rate γ↓** per stabilizer round, distinct for
  data vs measure qubits. **Use the measured values directly** as realistic teacher
  parameters (Table S1): no-reset γ↑ ≈ 0.09–0.11%/round, γ↓ ≈ 8–9%/round, p∞ ≈
  1–1.3%; with reset γ↓ jumps (22% data, ~328% effective measure). These are the
  order-of-magnitude targets for a faithful sim.
- **The dominant non-Pauli structural facts the teacher MUST encode** (these are
  *not* captured by any per-round Pauli channel):
  1. **Persistence / long lifetime.** Leakage decays on an energy-relaxation
     timescale, so it produces a **tail of detection events decaying over many
     rounds** (pg 4, Fig. 4) — a *temporal* correlation, not an i.i.d. per-round
     flip. γ↓ ≈ 8–9%/round ⇒ a leaked qubit survives ~10 rounds.
  2. **Mobility / transport.** A |2⟩ on a data qubit **hops to |3⟩ on a neighbouring
     measure qubit** through the CZ |21⟩↔|03⟩ resonance (pg 4) — a *spatial*
     correlation channel between qubits. The teacher needs an inter-qubit leakage-
     transport term tied to the two-qubit gate, not just on-site leakage.
  3. **Measurement-induced leakage.** Readout itself excites |2⟩ (measure qubits
     leak *more* than data qubits, Fig. 3) — leakage source must sit on the readout
     operation, not only on gates.
  4. **Random readout when leaked.** A leaked measure qubit gives detection-event
     fraction **0.5** (random outcome) (pg 4, Fig. 4a) — the natural soft-readout
     coupling: leakage manifests in the *measurement* channel.
- **Bounding an approximation.** The paper gives **semi-classical, closed-form
  bounds** for the coherent leakage dynamics (Landau–Zener): swap diabatic error
  `P_D^(s) ≪ exp[−(2πg)² t_swap/Δf]`, hold decay `exp(−κ t_hold)`, return
  `P_D^(r) = exp[−(2πg)²/ν_r]` (pg 2). If our teacher uses a **classical
  population-flow (Pauli + leakage-population) approximation** instead of a full
  qutrit/coherent sim, these are exactly the formulas that bound the error of
  ignoring coherence in the swap/return — and Fig. S3 quantifies the residual
  decomposition into computational (P1) vs leakage (P2+P3), telling us how much of
  the channel is in-basis (Pauli-correctable) vs genuinely leaked.

**(b) How to simulate leakage at scale.**
- The model is a **classical Markov rate process** on the leakage population
  (Eq. S1–S2) plus a **transport rule** on the two-qubit gate (|21⟩↔|03⟩,
  pg 4). This is cheap and scalable: it does **not** require a full qutrit density-
  matrix sim. A **Pauli + leakage-flag** stochastic simulator (each qubit carries a
  leaked/not-leaked classical flag that (i) is set by gate/readout with rate γ↑,
  (ii) clears with rate γ↓ per round, (iii) can transfer to a neighbour through a
  two-qubit gate, and (iv) forces a random/biased measurement outcome while set)
  reproduces all four signatures above and is Clifford-compatible (stabilizer-
  simulator-friendly), so it scales to large d. The validated-approximation question
  ("qutrit sim or validated approximation") is answered in our favour: the *observed*
  phenomenology (tail + transport + random-readout) is a population-level effect that
  a classical leakage-flag model captures, and the paper's own theory matches data at
  the population level (Fig. 2d/e, Fig. 3). The coherent fringes (Fig. 2b) are a
  reset-calibration artefact, not part of the code-level error process.

**(c) Neural decoder + soft/leakage input — what the signal looks like.**
- **The `pij` estimator (Eq. 1)** is a drop-in, calibration-free way to turn
  detection-event statistics into pairwise error-process probabilities — usable both
  as **decoder edge weights** (the paper feeds `pij` into MWPM, pg 6) and as a
  **diagnostic the decoder/teacher can be scored against**. Critically, **leakage
  shows up as long-range off-diagonal `pij` entries (>10 rounds)** (Fig. 5): a
  decoder that only consumes near-diagonal weights is **leaving headroom on the
  table** — this is precisely our "non-Pauli signal = decoding headroom above Pauli
  decoders" thesis, demonstrated on real hardware. A neural decoder that ingests the
  **full space-time syndrome volume** (rather than a matching graph with local
  weights) can in principle capture the long-range leakage correlations that MWPM-
  with-`pij` only partially absorbs.
- **Soft/leakage readout input** is concretely realisable: Fig. S4 is an **IQ
  scatter** separating |0⟩,|1⟩ from leakage; a decoder fed **analog IQ** (or a
  3-way soft label including a "leaked" class) has strictly more information than a
  hard 0/1 syndrome — the detection-event-fraction-0.5 signature (pg 4) is exactly
  the information a hard binarisation destroys. This supports building the teacher's
  readout channel to emit soft/leakage-aware observations and the decoder to consume
  them.
- **The checkerboard/odd-even control (Fig. S5, Supplement §IV)** is a useful
  *negative* control for our pipeline: the X-echo schedule produces a known,
  near-diagonal, odd-positive/even-negative correlation from plain energy
  relaxation. Our teacher should reproduce it, and our `pij`-based diagnostics must
  *not* mistake it for leakage; it is the baseline against which the long-range
  leakage tails are defined.
- **Decoder-gain framing.** The paper's headline metric — **Λ_bit 1.98 → 2.80** and
  faster stabilisation from removing time-correlated leakage (Fig. 6) — is the same
  axis we score on (%ΔLER / suppression). It quantifies *how much* correlated
  leakage costs in logical performance (here, the difference between a code that
  barely scales and one that scales meaningfully), i.e. an upper bound on the
  headroom a leakage-aware decoder competes for **if it must remove the leakage
  by decoding rather than by hardware reset**.

**Direct reuse checklist for the teacher/decoder:**
1. Leakage rate process: Eq. S1–S2 with Table S1 values (γ↑, γ↓ per round, data vs
   measure).
2. Transport channel: CZ |21⟩↔|03⟩ resonance (pg 4) → neighbour-hopping rule.
3. Measurement coupling: leaked measure qubit → random/biased readout (DEF 0.5,
   pg 4); soft IQ readout per Fig. S4.
4. Signatures to validate against: detection-event **tail** decaying over rounds
   (Fig. 4); long-range off-diagonal **`pij`** > 10 rounds (Fig. 5); odd-even
   **checkerboard** control (Fig. S5).
5. `pij` extraction: Eq. 1 (label-free, from detection-event moments).

---

## 6. Limitations and what does NOT apply to us

- **Bit-flip (repetition) code, not a 2D surface code.** All data are on a **1D
  21-qubit bit-flip chain** (Fig. 1b, Fig. 3 inset), a "simplified version of the
  surface code." The qualitative leakage phenomenology (lifetime, transport, tail,
  `pij` structure) should carry over to the surface code, but the **specific
  geometry of correlations** (which detectors a leaked qubit flips, the staggered-CZ
  adjacency) is 1D-specific. Our surface-code teacher must re-derive the spatial
  correlation graph for the 2D layout; only the *mechanism* transfers, not the
  matrix.
- **Reset is a hardware intervention, not a decoding result.** The paper's primary
  deliverable (the reset gate) **removes** leakage at the hardware level; our program
  is the opposite — we keep the leakage in the data as **decoding headroom**. The
  paper's value to us is the **"no-reset"** characterisation (the *signal*), not the
  reset gate itself. The reset-gate physics (§3.1, Fig. S1–S2, Landau–Zener bounds)
  is hardware-engineering detail largely orthogonal to a sim-only decoder program.
- **No qutrit/Lindblad microscopic error model is published here.** The leakage
  model is a **population rate equation** (Eq. S1–S2) plus a verbal transport
  mechanism; there is **no per-gate Kraus / qutrit channel** with which to build a
  first-principles simulator. We get rates and signatures, not a calibrated channel.
  (For canonical leakage Kraus channels / qutrit sims, we need other references —
  e.g. Wood–Gambetta, Varbanov ref [27], or a Pauli+leakage simulator framework.)
- **Decoder is plain MWPM with `pij` weights** (pg 6) — a **weak** baseline by our
  current bar (recall: Google's shipped corrMatch/harmony + RL-optimised prior
  already capture most correlation gains; per project memory, the contribution bar is
  beating the *shipped frontier*, not MWPM). The paper does **not** demonstrate a
  leakage-aware *decoder* — it removes leakage upstream and then decodes with a
  standard matcher. So it does **not** establish that a leakage-aware decoder beats a
  strong Pauli baseline; it only establishes that the leakage signal **exists and is
  large**.
- **Soft readout is used only for leakage discrimination at calibration**
  (Fig. S4), not as a decoder input. The IQ data is collected to *measure* leakage
  populations and the readout floor (by heralding), not fed to the matcher. The
  soft-input decoding idea is *enabled* by this hardware but **not done here**.
- **`pij` model assumes pair-flips.** Eq. 1 explicitly models detection events as
  arising from processes that flip **pairs** of measurements. Leakage actually
  produces **higher-order / many-round** correlations (the tail), which the pairwise
  `pij` only approximates. This is itself the headroom argument — but it means the
  `pij` matrix is a *lossy* summary of the leakage signal; a faithful teacher/decoder
  should not treat `pij` as the complete description.
- **Heavy postselection of "events."** ~0.8% of realisations are removed as
  anomalous high-detection "events" (Supplement §V) whose origin is "in preparation."
  These are exactly the rare correlated bursts a robust decoder might need to handle;
  the published logical numbers are *after* removing them, so they are an optimistic
  view of correlated-error handling.
- **Dated calibration constants.** All hardware numbers (g ≈ 120 MHz, η ≈ 200 MHz,
  κ ≈ 1/45 ns, idle 6.09 GHz, resonator 4.665 GHz, readout floor 0.2%) are
  specific to this 2020 Sycamore device. They are good order-of-magnitude anchors for
  a realistic teacher but should not be treated as universal.
```
