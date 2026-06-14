# Window-covering noise-model architecture (real XZZX)

> Design spine from the 2026-06-14 discussion. Plain record of the decisions; not a claim of results.
> Target: the noise twin on the **real Google XZZX surface code** (parsed from the real circuit), fit to
> **real hardware syndrome data**.

## Decisions

1. **Model = a FIELD of WINDOW channels** (refactor away from the per-qubit factorized model — that one
   structurally cannot carry correlated multi-qubit noise). **Each channel = one window's noise.**

2. **Window content = a weight-≤t MECHANISM composition** from the documented catalog
   (`docs/error_mechanisms.md`, M0–M34; channels in `forward/channels.py`), including the
   **correlated/coherent** mechanisms (M8 RZZ, M9 2q-depol, M10/M22–M33 parasitic couplings, M12
   correlated relaxation, M21 conditional phase). Applied to the window's ≤14-qubit density matrix.
   - This is tractable (params = mechanism strengths, ~linear in the window's gate count — NOT a dense
     2^(2·9) Choi), physically correct (matches the max correctable weight), and carries the **coherent
     slot** natively (density-matrix / Stinespring; coherent + non-Pauli + non-Clifford representable).

3. **Window scale = the code's correction limit** `t = ⌊(d-1)/2⌋` (d=7 → **t=3**). Rationale: the twin
   only needs to model noise accurately up to the **correctable** weight — beyond `t` errors the code
   fails regardless, so modeling it precisely does not help. Window radius `= ⌊t/2⌋` — the MINIMAL radius
   containing any connected weight-≤t config (a connected ≤t set has graph-RADIUS ≤ ⌊t/2⌋, not diameter
   t-1); d=7, t=3 → **radius 1** (a 3×3-scale window). Window `≤ 14` data qubits (the exact-backend wall).
   - Note: the window must also be `≥` the correlated-mechanism support (≥2 qubits); for d=7, `t=3 ≥ 2`,
     so `t` binds. For very small d this floor would bind instead.

4. **Cross-boundary error chains — handled by a COMPLETE COVERING** (the 2604.01197 (k+1)-layer
   constructive covering, applied to the trivial-phase **noise-channel field** — its valid scope). One
   window per data qubit = its **distance-≤⌊t/2⌋ neighborhood** ⇒ **every connected weight-≤t
   configuration is native to ≥1 window** (a connected ≤t set has a graph-CENTER member within distance
   ⌊t/2⌋ of all its members, so it sits inside the window centred on that center). **Computationally
   verified on real d7** (`outputs/window_covering.py`): 49 windows (≤5 qubits each), 347 connected ≤t
   configs, 0 uncovered.
   - This changes the fusion's job from "**reconstruct** cross-boundary chains (unbounded)" to
     "**reconcile** overlapping windows (bounded consistency)". Bigger windows do NOT solve cross-boundary
     chains (there is always a boundary); a complete covering does.

5. **Fusion = white-box recover + BLACK-BOX GNN composition (first-class).** Recover fits each window
   channel; the GNN composes them. The **GNN stays a first-class tool** (the scalable GPU realization of
   the composition). The covering gives it a **bounded, testable** problem (consistency-merge over a
   complete covering), so its risk — a-priori-unknown capability — is **managed** by fine-tuning /
   model iteration, **not** demotion. Calibrated against the Petz / exact-truth anchor (CF-WR).

6. **Coherent slot is native in each window channel** (density matrix); the composition must **preserve**
   it (CPTP + the coherent structure — the CF-WR composition-limit theory).

## Open (not assumed)

- **Multi-round forward** (the window channel is per-round; real data is multi-round on an evolving
  measured state). Two routes: **(A)** Pauli-twirl each window channel to a detector pattern + track the
  coherent residue separately (decoder is Pauli); **(B)** windowed reduced-density-matrix segments that
  keep coherence on small sub-circuits. To be decided when building the recover/forward.

## Build order

1. **Covering schedule** — given the real patch geometry + `t`, generate the window set with a verified
   completeness proof (`outputs/window_covering.py`).
2. **`WindowChannel`** — ≤14-qubit mechanism-composed channel + reduced-block / ρ_BC extraction.
3. **Single-window recover on real XZZX** — fit one window's channel to real hardware data.
4. **Composition** (white-box Petz anchor + the GNN), bounded by the covering.
