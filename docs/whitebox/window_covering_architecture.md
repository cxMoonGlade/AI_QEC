# Window-covering noise-model architecture (real XZZX)

> Design spine for the white-box noise model on the real Google XZZX surface code, fit to real hardware
> syndrome data. A design record, not a claim of results.

## Decisions

1. **Model = a FIELD of WINDOW channels.** Each channel = one window's noise, a multi-qubit CPTP map on
   the window's data qubits. This replaces the per-qubit factorized field (one independent single-qubit
   channel per data qubit), which structurally cannot carry correlated multi-qubit noise. **Runtime
   forward (D3):** the forward is the **faithful 6q 2×2-window Born likelihood** (4 data + 2 full-in
   ancilla = 6q at d3; ≤6q across all scales, never 8q — measured, `outputs/covering_2x2.py`), fit by
   a **composite likelihood**; the dense `WindowChannel` is the engine/oracle — see Multi-round forward
   below and [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md).

2. **Window content = a weight-≤t MECHANISM composition** from the catalog (`docs/error_mechanisms.md`,
   M0–M34; operators in `forward/channels.py`): the correlated/coherent mechanisms (M8 RZZ, M9 2q-depol,
   M10 RXX/RYY, M11 spectator crosstalk, M12 correlated relaxation, M21 conditional phase, M22–M33
   parasitic couplings) placed by local support, plus the 1q set, on the window's density matrix.
   Parameters = mechanism strengths (≈ linear in the window's gate count, not a dense 2^(2w)-dim Choi),
   so the channel is tractable, identifiability-friendly, and carries the **coherent slot** natively
   (density-matrix / Stinespring; coherent + non-Pauli + non-Clifford representable).

3. **Window = the 2×2 data block + its full-in stabilizer(s).** A weight-4 XZZX plaquette covers a 2×2
   data block; the faithful window is those 4 data qubits together with every ancilla qubit whose
   stabilizer is fully internal to that block. Ancilla cannot be eliminated: noise lives on the
   data⊗ancilla entangled state before measurement, so dropping the ancilla loses the very coherence the
   white-box exists to recover. **Measured register: 4 data + 2 full-in ancilla = 6q at d3** (≤6q across
   all scales, never 8q — (a)-exact, `outputs/covering_2x2.py`), within the exact-backend wall.

4. **Cross-boundary error chains — handled by a COMPLETE COVERING.** One 2×2 window per plaquette ⇒
   **every connected weight-≤t configuration is native to ≥1 window**: a connected ≤t set has a member
   within graph-distance 1 of all its members (e.g. a 3-chain's middle qubit), so the whole set sits in
   some window's plaquette. (2604.01197's (k+1)-layer constructive covering, applied to the trivial-phase
   **noise-channel field** — its valid scope.) **No seam-only stabilizers exist at the 2×2 scale**:
   every stabilizer is full-in ≥1 window (d3 8/8, d5 24/24, d7 48/48 — (a)-exact, `outputs/covering_2x2.py`).
   Fusion is therefore a **bounded consistency-merge via cross-window data-consistency over shared data
   (overlap ≤4) + the long-range/cross-window correlations (residual budget)**, not a seam-stabilizer
   absorption problem. Bigger windows do not remove cross-boundary chains (there is always a boundary);
   a complete covering does. The schedule is generated from the **parsed stabilizer supports** of the real
   circuit (build-order step 1). The covering choice is **footprint-feasibility** until the conditioned
   multi-round forward and the composite Fisher `H` are in hand, then **Fisher-optimal** (maximise
   `rank(H)` at the nominal θ) —
   see [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §11.3.

5. **Fusion = white-box recover + BLACK-BOX GNN composition, engaging from d3.** Recover fits each 2×2
   window channel; the GNN composes them over the covering from d3 onward **via cross-window
   data-consistency over shared data (overlap ≤4) + the long-range/cross-window correlations (residual
   budget)** — there are **no seam-only stabilizers** at the 2×2 scale (every stabilizer is full-in ≥1
   window — (a)-exact, `outputs/covering_2x2.py`). The GNN is a **first-class tool** (the scalable GPU
   realization of the composition); the covering gives it a bounded, testable problem
   (consistency-merge), calibrated against the Petz / exact-truth anchor (CF-WR). Its output is a
   calibrated band, never a premise.

6. **Coherence preserved END-TO-END.** Each window channel carries coherence natively (density matrix);
   the composition must preserve it (CPTP + coherent structure — the CF-WR composition-limit theory).
   The twin does **not** twirl down to Pauli. Pauli/DEM appears only as a **lossy downstream export**
   when feeding a Pauli decoder (e.g. an MWPM LER evaluation), a property of *that decoder*, band-
   tracked, never the twin's representation — and that residual (what a Pauli decoder discards) is itself
   a reportable result. RECOVER + validation are syndrome-NLL, hence decoder-independent, so the whole
   fit+validate loop preserves coherence.

7. **The hard core = coherent cross-window composition (the seam).** Stitching adjacent windows' coherent
   CPTP channels into one globally consistent, CPTP, coherence-preserving field is the
   CF-WR / Petz / `ρ_BC` problem. The covering downgrades it from unbounded reconstruction to a bounded
   consistency-merge, but it stays the hardest link. The architecture in one line: **fidelity** = native
   coherence inside each window; **correctness** = the covering makes the fusion bounded and verifiable.

## Multi-round forward (D3: conditioned multi-round detector-record likelihood)

The window channel is single-round; real data is multi-round on a measured, evolving state. The forward
fits the coherent window channels to the real multi-round **detector record** via window-local
record-conditioned spacetime likelihoods.

**Runtime forward (D3).** The forward is the **syndrome-conditioned multi-round detector-record
likelihood** on the 6q 2×2 window (4 data + 2 full-in ancilla = 6q at d3; ≤6q across all scales, never
8q — measured, `outputs/covering_2x2.py`): from the real reset boundary, propagate the `R = 90` rounds
on the dense oracle with the **recorded** ancilla outcomes (per round: noisy gates → project the ancilla
on its recorded outcome → renormalize → reset; the verified single-round projector core called R times),
accumulating `log P_θ(record)` per window in the log domain (boundary rounds prep/readout modeled
distinctly); fit by the **composite likelihood** `ℓ(θ) = Σ_j log P_θ(record_j)` over held-out shots, on
the real non-unital `detection_events.b8`. The dense `WindowChannel` is the engine and correctness
oracle. (A 9q data-register + per-stabilizer measurement instrument approach was tried and falsified —
retired. See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) for the full design.) The
register size and cost are measured on the real data, not assumed.

**Why conditioned-and-multi-round, on real (non-unital) data — not the unconditional stationary state.**
The earlier draft evaluated the forward on the unconditional **stationary state of the syndrome-AVERAGED
round `ρ_ss(θ)`**. That is degenerate for the unital SI1000 prior: `ρ_ss = I/16` exactly and
θ-independent (`outputs/w2x2_window_rho_ss.py`) ⇒ the Fisher collapses to `rank(H) = 1`. The information
is carried only by **(a)** the **non-unitality** of the real device channel (T1 / leakage moves the
fixed point off `I/16`) and **(b)** the **multi-round** temporal structure of the conditioned detector
record; conditioning alone does not rescue it (a single-round conditioned forward is also rank-1 under
unital noise). Coherent mechanisms (RZZ/RXX — unital) are invisible to any stationary state and
identifiable only in the conditioned multi-round record. The unital-stationary case is kept as the
**negative control**. See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §2.0 for the
full derivation.

## Scale mapping — d3 → d7 → d5 (D1)

The white-box / black-box split maps to the dataset's three distance rungs, but the execution order is
**d3 → d7 → d5**: certify the 2×2 white-box and the first black-box composition simultaneously at d3,
then validate the seam at d7, then use d5 as the intermediate-scale interpolation rung.

| Rung | Distance | Dataset object | Description | Build step |
|---|---|---|---|---|
| White-box + black-box | **d=3** | 9 standalone `d3_at_q*` patches | Each d3 patch covered by overlapping 2×2 windows (4 data + 2 full-in ancilla = 6q per window — measured, `outputs/covering_2x2.py`; no seam-only stabilizers — every stabilizer is full-in ≥1 window, d3 8/8 (a)-exact). Per-window fit (6q faithful, per-window identifiability ceiling = 2 syndrome bits): held-out syndrome NLL + Fisher rank + alias band. Black-box GNN composes the 2×2 windows via cross-window data-consistency + residual budget into the d3 patch from this rung. | step-3 + step-4 |
| Seam validation | **d=7** | `d7_at_q6_7` (49 windows + real seam) | The black-box (GNN + Petz) composes per-window channels across the real d7 seam into a globally consistent, coherence-preserving field; validated by held-out syndrome NLL and %ΔLER under a frozen decoder. | step-4 (extended) |
| Intermediate validation | **d=5** | 4 patches | Post-d7 sanity / interpolation rung; structural checks (20/20 cross-check) confirmed same facts hold. | step-5 (after d7) |

This realises Decision 5 (white-box recover + black-box GNN composition from d3) and build order
step-3/4 with d5 retained as a post-d7 validation rung rather than a gate before d7.

## Own-data-per-scale principle (D2)

Each scale fits its white-box from its **own** data; no cross-scale parameter transfer occurs:

- d3 white-box is fit on d3 syndrome data.
- d7 per-window white-box fit uses d7's own data (through the seam).
- The black-box **composes** already-fitted window channels — it does not import d3 parameters into
  d7.

Rationale: `d3_at_q6_7` and the d7 `(6,7)` interior window are the same physical qubits (step-1 a7:
exact coord match), but they are **different hardware runs** (different `.stim`, different syndrome
data, different crosstalk neighbourhood). Fitting each scale from its own data avoids an unproven
assumption that internal mechanisms transfer across d3/d7 context, and keeps d7-failure attribution
clean (black-box composition error, not white-box transfer error).

## Build order

1. **Covering schedule** — from the parsed stabilizer supports of the real circuit: the 2×2 windows
   (each plaquette's 4 data qubits + full-in ancilla) + the computational completeness check.
2. **`WindowChannel`** — the multi-qubit mechanism-composed CPTP channel + reduced-block / `ρ_BC`
   extraction.
3. **Per-2×2-window recover on real XZZX** — fit each 2×2 window channel (6q faithful at d3; ≤6q all
   scales, never 8q — measured, `outputs/covering_2x2.py`) over the
   overlapping windows covering each d3 patch (no seam inside a window; the seam between windows is
   the black-box's). Per-window `rank(H)` is limited (~1 full-in stabilizer/window) — most
   identifiability is earned by the black-box composing overlapping windows (step 4).
4. **Composition — black-box GNN, FROM d3** — white-box Petz anchor + black-box GNN, bounded by the
   covering; composes the overlapping 2×2 windows **via cross-window data-consistency over shared data
   (overlap ≤4) + the long-range/cross-window correlations (residual budget)**; **no seam-only
   stabilizers** (every stabilizer is full-in ≥1 window — (a)-exact, `outputs/covering_2x2.py`);
   **at d3 first, then d7** (49 windows + real seam).
5. **d5 validation** — rerun the own-data-per-scale checks on d5 as the intermediate-scale sanity /
   interpolation rung after d7.
