# understand — [UNDERSTAND]  (placeholder)

Interpret a recovered channel field `E_hat` into human-meaningful mechanism terms:
which mechanism at each location, its strength, coherent-vs-stochastic type, axis.
The model's interpretation / readout capability.

**Status: placeholder** — the interpretation logic is future work; the module name
is reserved as a core-capability slot.

**Boundary.** The evaluator-side identifiability / uncertainty machinery is NOT
here — it lives in `audit` (gating, bands, validity). `understand` is the model's
own readout of the recovered channel. Spec: `docs/TWIN.md`.
