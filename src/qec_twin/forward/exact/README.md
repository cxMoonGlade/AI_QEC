# forward/exact — density-matrix backend  ⚠ FEASIBILITY-ONLY

Exact, differentiable density-matrix simulation of the noisy circuit.

- `circuit_sim.py` — exact `p(y|c) = Tr[M_y C(c)(rho0)]` forward.
- `rep_code.py` — multi-round repetition-code instrument forward (trajectory-enumerated `p(s,m)`; ancilla + data-only parity backends).
- `density_sim.py` — density-matrix / Kraus application primitives.
- `born_local.py` — local Born-rule diagnostics.

**Boundary (hard).** The density matrix is `2^n × 2^n`. This backend exists ONLY to
validate the B-path counterfactual loop at small scale (≤ ~15 qubits). The target
is 50+ qubit hardware noise circuits, where this **explodes** — it must be replaced
by `forward/scalable/` once feasibility is confirmed. Do not build production or
real-data paths on this backend.
