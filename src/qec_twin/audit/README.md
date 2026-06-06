# audit — evaluator-side identifiability / uncertainty / validity

**Non-core.** Evaluator-side assessment of the recovered model: what is
recoverable, how uncertain the answer is, and whether a knob is trustworthy. These
ASSESS the four capability modules; they are not themselves a model capability
(hence not under the model core).

- `gating.py` — identifiability gating: anchor features, learnable-DOF deficiency,
  Girsanov (Pauli-vs-coherent) split (D5).
- `bands.py` — alias / uncertainty bands on ΔLER (Tier-0 Laplace ellipsoid) (D3).
- `validity.py` — counterfactual-validity curve (calibrate-on-`r≤k` / predict
  held-out exotic) + negative controls (D2/D4).

**Boundary.** Evaluator-only. May read teacher ground truth to *score* validity;
never feeds the learner. Spec: ADR 0003 / 0004, `docs/TWIN.md`.
