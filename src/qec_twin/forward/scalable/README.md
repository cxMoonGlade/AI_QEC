# forward/scalable — scalable forward backend  (placeholder)

Reserved for the >50-qubit forward model that replaces `forward/exact` after the
B-path feasibility loop is validated. Density-matrix simulation does not scale; the
target hardware noise circuits exceed 50 qubits.

**Status: placeholder** — no carrier chosen yet (candidates: tensor-network
contraction, DEM-bulk + local coherent corrections, …). Scalability is a deferred
selection criterion (ADR 0009).

**Contract.** Must satisfy the same `forward` contract `context c → p(s,m|c)` so
that `calibration` / `knobs` / `understand` / `prediction` are unchanged when the
backend is swapped in.
