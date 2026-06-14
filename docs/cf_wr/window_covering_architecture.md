# Window-covering noise-model architecture (real XZZX)

> Design spine for the white-box noise model on the real Google XZZX surface code, fit to real hardware
> syndrome data. A design record, not a claim of results.

## Decisions

1. **Model = a FIELD of WINDOW channels.** Each channel = one window's noise, a multi-qubit CPTP map on
   the window's data qubits. This replaces the per-qubit factorized field (one independent single-qubit
   channel per data qubit), which structurally cannot carry correlated multi-qubit noise.

2. **Window content = a weight-≤t MECHANISM composition** from the catalog (`docs/error_mechanisms.md`,
   M0–M34; operators in `forward/channels.py`): the correlated/coherent mechanisms (M8 RZZ, M9 2q-depol,
   M10 RXX/RYY, M11 spectator crosstalk, M12 correlated relaxation, M21 conditional phase, M22–M33
   parasitic couplings) placed by local support, plus the 1q set, on the window's density matrix.
   Parameters = mechanism strengths (≈ linear in the window's gate count, not a dense 2^(2w)-dim Choi),
   so the channel is tractable, identifiability-friendly, and carries the **coherent slot** natively
   (density-matrix / Stinespring; coherent + non-Pauli + non-Clifford representable).

3. **Window = the 3×3 block around each data qubit.** Scale = the code's correction limit
   `t = ⌊(d-1)/2⌋` (d=7 → t=3): the twin only needs to model noise up to the correctable weight; beyond
   `t` the code fails regardless. The block is the radius-`⌊t/2⌋` = 1 ball in the **share-a-stabilizer
   graph** — two data qubits are adjacent iff some stabilizer's support contains both. A weight-4
   plaquette covers a 2×2 data block, so each data qubit is adjacent to all eight grid-neighbours
   (orthogonal **and** diagonal); the radius-1 ball is therefore the **3×3 block = ≤9 data qubits**
   (9 interior, fewer at the boundary). Within the ≤~15-qubit exact-backend wall.

4. **Cross-boundary error chains — handled by a COMPLETE COVERING.** One 3×3 window centered on every
   data qubit ⇒ **every connected weight-≤t configuration is native to ≥1 window**: a connected ≤t set
   has a member within graph-distance `⌊t/2⌋` = 1 of all its members (e.g. a 3-chain's middle qubit), so
   the whole set sits in that member's 3×3 window. (2604.01197's (k+1)-layer constructive covering,
   applied to the trivial-phase **noise-channel field** — its valid scope.) Fusion is then a **bounded
   consistency-merge** over overlapping windows, not an unbounded reconstruction of cross-boundary
   chains. Bigger windows do not remove cross-boundary chains (there is always a boundary); a complete
   covering does. The schedule is generated from the **parsed stabilizer supports** of the real circuit
   (build-order step 1).

5. **Fusion = white-box recover + BLACK-BOX GNN composition.** Recover fits each window channel; the GNN
   composes them over the covering. The GNN is a **first-class tool** (the scalable GPU realization of
   the composition); the covering gives it a bounded, testable problem (consistency-merge), calibrated
   against the Petz / exact-truth anchor (CF-WR). Its output is a calibrated band, never a premise.

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

## Multi-round forward

The window channel is single-round; real data is multi-round on a measured, evolving state. The forward
fits the coherent window channels to real multi-round detector data via **window-local coherent
spacetime marginals**: a single window's data + ancilla register evolved exactly across rounds with
per-round ancilla measure/reset (each observed shot = one projector trajectory; coherence retained),
within the exact-backend wall. The register size and cost are measured on the real data, not assumed.

## Build order

1. **Covering schedule** — from the parsed stabilizer supports of the real circuit: the 3×3 windows
   centered on each data qubit + the computational completeness check.
2. **`WindowChannel`** — the multi-qubit mechanism-composed CPTP channel + reduced-block / `ρ_BC`
   extraction.
3. **Single-window recover on real XZZX** — fit one window's channel to real hardware syndrome data.
4. **Composition** — white-box Petz anchor + black-box GNN, bounded by the covering.
