# Surface noise model — measured real structure + mechanism-based direction

> The rotated-CSS toy is removed (it was a synthetic stand-in; the real code is XZZX). This records the
> **measured real d3 XZZX structure** and the **mechanism-based** model direction grounded in the
> documented catalog (`docs/error_mechanisms.md`). Plain reporting — measured facts only.

## 1. Measured real structure — `outputs/surface_d3_structure.py`

Real set2 `d3_at_q5_5/X/r15` sample_00 (60k shots, decoder-independent; detection events + circuit only):

- detection ~6.3%/detector;
- 2-body correlation sits **on the matching graph** (0 far/non-edge pairs above 5σ);
- **device vs the shipped SI1000 sim: detection 2.4×, edge-pij 3.6×, 3-body cumulant 2×** — 467/600
  matching-graph triangles carry a 3-body cumulant clearly above the `1/N` noise floor.

So the real device is noisier, more correlated, and **higher-order beyond the sim**. (Self-correction:
an earlier "overdispersion 2.29× = bunched" read was wrong — syndrome-weight variance is only a 2-point
quantity; the honest test is measured-vs-model, above.) One instance; not a sweep.

## 2. The 3-body is documented + implemented (not a discovery)

The correlated/higher-order structure is the project's **documented mechanism catalog**
(`docs/error_mechanisms.md`, 35 mechanisms M0–M34), implemented as channels in
`src/qec_twin/forward/channels.py` (`mechanism_channel`) + `mechanisms/catalog.py`. The measured
2-body/3-body is produced by the correlated/multi-qubit mechanisms — **M8** RZZ, **M9** 2q depolarizing,
**M10** RXX/RYY, **M11** spectator crosstalk, **M12** correlated relaxation, **M21** conditional phase,
**M22–M33** parasitic couplings, plus the G2/G3 families. (Doc path note: the catalog's
`primitives/mechanism_catalog.py` reference is stale — code is at `forward/channels.py` +
`mechanisms/catalog.py`.)

## 3. Model direction (registration §3)

A **circuit-level noise model over the mechanism catalog** — correlated/coherent mechanisms attached to
the real XZZX circuit's gates, strengths fit to the real syndrome data — NOT a generic per-qubit
independent channel (the wrong model class, now retired). Honest challenge: coherent + multi-round +
17-qubit circuit exceeds the exact backend / stim-Pauli scope; the build must state its approximation
(windowed density-matrix segments / Pauli-twirl-plus-coherent-residue), not dodge into a toy.

## 4. Errors corrected (this thread)

- rotated-CSS toy → real XZZX (the real code is XZZX, 8/8 mixed stabilizers).
- per-qubit independent model + synthetic independent-Pauli teacher → mechanism-based correlated model
  (the real noise is correlated, per the catalog + the measurement).
- "recovery validated / machine-exact / capstone" inflation → plain measured reporting.
- single-round exact CPTP forward acknowledged as unable to fit real multi-round data.

## 5. Status & next

Structure measured (§1); model grounded in the mechanism catalog (§2–§3). **Next:** build the
mechanism-based noise model on the real XZZX circuit, fit to real d3 syndrome data, validate by held-out
NLL + the structure-residual (does it reproduce the measured detection / 2-body / 3-body).
