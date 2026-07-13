# decoder — frozen-MWPM DEM substrate

The minimal DEM machinery for the **frozen** decoder used to compute the logical
error rate (LER) that knobs act on. Frozen = predeclared, never retuned inside a
knob or validity score.

- `stim_dem.py` — stim detector-error-model extraction.
- `fault_graph.py` — canonicalized DEM parity-map graph.
- `parity_map.py` — DEM parity map `A ∈ F_2^{B×M}`.

**Boundary.** A fixed MWPM reference substrate only — not a learned object, not the
twin's recovered channel. Used by `knobs` (ΔLER) and `audit`. This is all that
survives of the retired DEM/Bernoulli fault-logit program (ADR 0005).
Spec: `docs/TWIN.md`.
