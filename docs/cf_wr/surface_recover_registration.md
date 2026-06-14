# Surface noise model on REAL XZZX d3 — registration

> **The surface code is XZZX, not CSS.** This supersedes the earlier rotated-CSS controlled toy
> (removed — it was a synthetic stand-in; the real Google d3 is XZZX: 8/8 mixed stabilizers, parsed
> from the real circuit). The object now is the noise twin on the **real XZZX surface code**, fit to
> **real hardware syndrome data**, informed by the **measured** real structure — not a synthetic toy.

## 1. Geometry — parsed from the real circuit (no synthetic code)

The model reads the stabilizers/logical from the real d3 `circuit_ideal.stim` (e.g. set2
`d3_at_q5_5`): 9 data qubits; **8 mixed XZZX stabilizers** (bulk weight-4 `X-Z-Z-X`, boundary weight-2
mixed); logical from `OBSERVABLE_INCLUDE`. d3 = 9 data = 2⁹ fits the exact backend; the stabilizers are
Hermitian / square-to-I / mutually commuting (verified), so the syndrome machinery carries over.

## 2. Measured real structure (the model target — `outputs/surface_d3_structure.py`)

On real set2 `d3_at_q5_5/X/r15` sample_00 (60k shots, decoder-independent), measured vs the shipped
SI1000 sim:
- detection ~6.3%/det; 2-body correlation sits **on the matching graph** (0 far pairs above 5σ);
- **device vs SI1000: detection 2.4×, edge-pij 3.6×, 3-body cumulant 2×** (467/600 matching triangles
  carry real 3-body) — the device is noisier, more correlated, and **higher-order beyond the sim**.

**Implication (decides the model class):** an **independent-edges** model is insufficient (real 2-body
+ 3-body); even the SI1000 sim (already 59% hyperedges) under-predicts. The model must carry
**correlations** and the higher magnitude. This is the M4 lesson, now measured on surface.

## 3. The model — built on the implemented mechanism catalog (M0–M34)

The noise is correlated — that is **not** a question to rediscover, it is **documented + implemented**:
`docs/error_mechanisms.md` enumerates 35 mechanisms (legacy M0–M34); the channels are implemented in
`src/qec_twin/forward/channels.py` (`mechanism_channel(spec)`) + `mechanisms/catalog.py`. (NB: the doc's
`primitives/mechanism_catalog.py` path is **stale** — the code lives at `forward/channels.py` +
`mechanisms/catalog.py`.) The measured 2-body/3-body structure is produced by the **correlated /
multi-qubit** mechanisms: **M8** (RZZ), **M9** (2q depolarizing), **M10** (RXX/RYY), **M11** (spectator
crosstalk), **M12** (correlated relaxation), **M21** (conditional phase), **M22–M33** (parasitic XX/YY/
XY/ZX/… couplings), plus the G2/G3 families.

So the model is **a circuit-level noise model over this mechanism catalog**: mechanisms (incl. the
correlated/coherent ones) attached to the real XZZX circuit's gates, with strengths **fit to the real
syndrome data** (the RECOVER capability applied to the catalog) — NOT a generic per-qubit independent
channel (that was the wrong model class).

**Honest challenge (the real difficulty, not dodged into a toy):** the catalog includes coherent /
non-Pauli mechanisms (M6–M8, M10, M21–M33); the real instance is a multi-round 17-qubit (9 data + 8
ancilla) circuit. A full exact density-matrix sim with coherent mechanisms over many rounds is at/over
the ≤15q backend wall, and stim (Pauli-only) cannot carry the coherent terms. The model build must
confront this (windowed / per-round density-matrix segments, or a Pauli-twirled approximation with the
coherent residue tracked separately), and state the approximation honestly.

## 4. Validation (real data — no synthetic ground truth)

Held-out per-shot syndrome **NLL** on real data + the **structure-residual** check (does the fitted
model reproduce the measured 2-body and 3-body). There is no exact "recovery vs teacher" on real data;
claims are observation-fit + residual structure, stated plainly.

## 5. Discipline

Real data; `sample_00` training, held-out reserved; decoder-independent for the structure read; the
shipped `decoding_results/` priors are evaluator/baseline-only, never learner input. GPU; scripted-
execution. Plain reporting — no "validated/machine-exact/capstone" inflation; state what is measured.

**Deliverables:** `outputs/surface_d3_structure.py` (the measured structure, done); the real-data
detector-level model + the independent-vs-correlated decision (next); results in
`docs/cf_wr/surface_recover_RESULTS.md`.
