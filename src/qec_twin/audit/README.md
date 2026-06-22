# audit — evaluator-side identifiability / uncertainty / validity

**Non-core.** Evaluator-side assessment of the recovered model: what is
recoverable, how uncertain the answer is, and whether a knob is trustworthy. These
ASSESS the four capability modules; they are not themselves a model capability
(hence not under the model core).

- `gating.py` — identifiability gating: anchor features, learnable-DOF deficiency,
  Girsanov (Pauli-vs-coherent) split (D5); the H2 W2 edge DOF gate
  (`edge_dof_gate`, ADR 0006 3(i) — runs before any fit).
- `bands.py` — alias / uncertainty bands on ΔLER (Tier-0 Laplace ellipsoid) (D3);
  includes the coupled twin's `phi_hat` direction and edge (`target_edge`) knobs.
- `validity.py` — counterfactual-validity curve (calibrate-on-`r≤k` / predict
  held-out exotic) + negative controls (D2/D4).
- `bayes_floor.py` — the model-free **Bayes decoding floor** `F(R)=Σ_s min(P(s,f=0),P(s,f=1))`
  (the gap-to-optimum denominator). `mc_floor` is the UNBIASED exact-per-sample Monte-Carlo floor
  (Born-branch the DM, read `P(f|s)` exactly per sample — no in-sample-plug-in down-bias),
  `enumerate_floor` the exact R=1 anchor, `plugin_floor`/`crossfit_floor` the valid bracket,
  `floor_convergence_report` the no-drift tripwire. GPU-only. Spec:
  `docs/nonpauli_teacher/p7b_estimable_floor.md`; ledger `tests/test_bayes_floor.py` (L1/L2/L3/L6).
- `floor_backend.py` — the `PathJointEvaluator` Protocol (the 6 floor seams) + `DMPathEvaluator`,
  the certified dense `3^n` density-matrix backend (the d3 oracle; faithfulness established
  component-wise by the #11 L1 independent lane vs the raw `.stim` + a from-scratch oracle —
  schedule byte-identical, leak dynamics |2⟩(R) to 1.4e-15, WG slice exp(L/4) to 1.75e-13,
  ⟨S⟩/logical/detectors vs stim; the `1.5e-18` is the parsing/geometry cert, not a DM-output
  distribution residual). The
  floor logic is backend-agnostic; the evaluator supplies the per-record syndrome-conditioned
  `(s,L)` sector weights (ADR 0010 §Integration item 8b).
- `floor_backend_tn.py` — `TNPathEvaluator`, the **scalable quimb LPDO** floor backend (ADR 0010
  task 8d): the same `PathJointEvaluator`, carrying `ρ = X X†` as a locally-purified MPDO
  (positivity STRUCTURAL — never plain MPO, C2). Matches `DMPathEvaluator` bit-for-bit at full χ
  (the C8 anchor); a truncated χ bounds the bonds with tracked discarded weight (the class-(a)
  state ledger). GPU-only. Self-validation: `outputs/teacher_prereg/p7d_lpdo_floor_selfval.py`;
  full-9q rung-2 certification + the χ-convergence curve is task 8e.

**Boundary.** Evaluator-only. May read teacher ground truth to *score* validity;
never feeds the learner. Spec: ADR 0003 / 0004, `docs/TWIN.md`.
