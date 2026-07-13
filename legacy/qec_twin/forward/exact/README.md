# forward/exact — density-matrix backend  ⚠ FEASIBILITY-ONLY

Exact, differentiable density-matrix simulation of the noisy circuit.

- `circuit_sim.py` — exact `p(y|c) = Tr[M_y C(c)(rho0)]` forward.
- `rep_code.py` — multi-round repetition-code instrument forward (trajectory-enumerated `p(s,m)`; ancilla + data-only parity backends).
- `steady_state.py` — exact stationary detector-block law of a rep-code window (non-selective `dephase_parity` burn-in + enumerated rounds; R2-lite M3).
- `circuit_sim.dephase_parity_sweep` — fused full-sweep parity dephase (one cached 0/1-mask multiply per round; contract: IEEE-`==` bit-exact to the sequential `dephase_parity` j-loop, forward and gradients — pinned by `tests/test_steady_state_fusions.py`).
- `density_sim.py` — density-matrix / Kraus application primitives.
- `born_local.py` — local Born-rule diagnostics.

**Boundary (hard).** The density matrix is `2^n × 2^n`. This backend exists ONLY to
validate the B-path counterfactual loop at small scale (≤ ~15 qubits). The target
is 50+ qubit hardware noise circuits, where this **explodes** — it must be replaced
by `forward/scalable/` once feasibility is confirmed. Do not build production or
real-data paths on this backend.
