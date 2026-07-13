# METRICS — the simulator metric ledger

The canonical, **stable** definitions of every evaluation metric in
`error_coupling_simulator`, each with its field-standard name, literature reference, and the
convention carried with it. Binding framing: `docs/SIMULATOR.md`. This ledger exists so a
metric can never be reasoned about under a wrong label or a silent non-standard stand-in.

> The twin-era learner ledger (calibration NLL / identifiability / `do()`-counterfactual /
> decision-regret metrics) is archived at `docs/_archive/METRICS.md` — out of scope here.

## The rule — metric choice is a forced ladder

**Every quantitative claim is scored by a field-standard metric, chosen by this ladder; no rung
may be skipped and no non-standard stand-in used silently.**

1. **Use a metric in this ledger** — by its field-standard name, reference, and convention.
2. **If none fits, research the frontier first** — find the field-standard metric in the recent
   literature (RAG over `docs/papers/reading_notes/`; KG), **add it to this ledger** (name +
   reference + convention), and use it.
3. **Only if none exists, create one — and flag it** as **project-defined / non-standard**,
   justified, carried as a debt pending a standard-naming pass. A created metric is a debt, not a
   default.

## Epistemic-status declaration (standing rule)

Every quantitative item declares one of three classes (`docs/FAITHFULNESS_PROTOCOL.md`):

- **(a) exact** — a theorem, algebraic identity, or zero-tolerance check. The ONLY class that may
  serve as a premise, definition, or derivation step.
- **(b) prediction band** — a pre-registered falsifiable bet; a miss is a finding, never later
  citable as fact.
- **(c) heuristic gate** — a threshold / convention / margin; permitted for pre-registered go/no-go
  gating ONLY, forbidden as a premise, bound, or basis for any conclusion.

An undeclared item defaults to (c). Every d5/d7 distributional number is **PROVISIONAL** (no
external oracle exists above the d3 exact-DM referee) — reportable and gate-usable, never built upon.

## Conventions throughout

- **Units:** information quantities in **nats** (natural log) unless a metric names bits; LER / ΔLER
  / ε_d are probabilities.
- **Numerical floor:** `NUMERICAL_ZERO = 1e-12` for `log(0)` / reachable-branch masking
  (`error_coupling_simulator.numerics`); never for structural zeros.
- **Frozen decoder:** all LER / ΔLER / %ΔLER are scored under one frozen, predeclared, named decoder
  (PyMatching/MWPM); the decoder is never refit per channel.
- **The record is the validity target (ADR 0011):** faithfulness gates on §1 (the record); §2
  (carrier bond / truncation) is a **feasibility/cost** guard only, never the validity target.

---

## 1. Record faithfulness — the validity target

Does the emitted multi-time syndrome record match an INDEPENDENT reference distribution? Scored at
d3 vs the exact-DM oracle; the RECORD is what feasibility gates on (ADR 0011).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Syndrome-distribution total-variation | `½‖p − q‖₁` over the record support | **total-variation distance** (Nielsen & Chuang 2010 §9; `P_e = ½(1−TV)` Bayes link, Nielsen arXiv:1401.4788) | (a) at exact enumeration; (b) finite-sample | over the joint `(detectors, obs)`; the field-standard distance for comparing two distributions — never element-wise `max` |
| Record relative entropy | `KL(p_ref ‖ p_carrier) = H(p_ref,p_carrier) − H(p_ref) ≥ 0` | **relative entropy / KL** (Cover & Thomas 2006) | (a) population / (b) finite-sample | nats; `KL→0` ⇔ the record distributions agree |
| Held-out per-shot syndrome NLL | `−(1/N) Σ_n log p(y_n)` | **held-out negative log-likelihood** — the dMLE model-scoring objective (Cao et al. arXiv:2602.19722; population limit = the cross-entropy, Cover & Thomas 2006) | (b) | per shot, nats; held-out split declared before scoring; bootstrap CI; identical splits across models |

**Verification-vs-claim guard (binding).** Comparing two INDEPENDENT computations of the *same*
`P(record)` (a cross-check) may report `max|A−B|` (L∞) as a machine-agreement diagnostic; comparing
*distinct* distributions (carrier vs oracle, model vs baseline) ALWAYS uses TV / KL / NLL — never the
element-wise max (which masks distributional failure).

---

## 2. Carrier / truncation convergence — feasibility & cost (NOT the validity target)

Bounds the **state / representation cost**, not the record or the LER (ADR 0010/0011). A carrier
number here gates resources and internal convergence only; the faithfulness claim lives in §1/§3.

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Per-cut discarded weight | `ε_cut = Σ_{i>χ} σ_i²`, with `‖ψ − ψ_χ‖² = ε_cut` | **Schmidt truncation identity** (standard; ADR 0010 constraint ledger) | (a) exact (bounds the STATE, not the LER) | per bond cut; accumulates `1 − F ≤ Σ_t ε_cut^{(t)}` over the trajectory |
| Truncation error (SVD) | `2-norm of the truncated singular-value vector` = `√ε_cut` | dynamic-threshold MPS/TN truncation control (Manabe–Suzuki–Darmawan arXiv:2308.08186; `reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md`) | (c) gate | bond `χ` chosen dynamically to hold it below a declared threshold (their 1e-6 rep / 1e-4 surface) |
| χ-convergence | record statistic (§1) vs `χ`, anchored to the d3 DM oracle; a `χ*` exists + monotone | **convergence-in-χ self-consistency** (the L2 no-drift test; ADR 0010 Rung 3; Manabe Fig. 6 area-law bond saturation) | (b) at d3 / (c) extrapolated | licenses d5/d7 where no oracle exists; a drift as `χ` grows ⇒ NOT converged ⇒ STOP |
| Average bond dimension | `mean χ` per round | representation **cost proxy** (Manabe 2308.08186 Figs 5–7) | (c) | resource guard only; saturates over rounds under area law |
| Leakage / seepage rate | `L1, L2` (leaked-population growth / return) | leakage & seepage rates (Wood–Gambetta; Manabe 2308.08186 Eq. 14–15 diagnostic) | (c) diagnostic | qutrit `\|2⟩` mass; a leakage diagnostic, not a record observable (ADR 0011 Context) |

**⚠ Do not gate faithfulness on this section.** Truncating on the singular-value/bond (Manabe's
threshold) bounds the *state*; ADR 0011 gates feasibility on the *record* (§1). The coherent leakage
tail inflates `χ` but carries zero record content — it is dropped (record-faithful truncation).

---

## 3. Channel / process distances — carrier certification at d3

Channel-level cross-checks of the carrier against the exact-DM / from-scratch oracle (Rung 0–1).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Process (entanglement) infidelity | `1 − F_e`, `F_e` = Uhlmann fidelity of the trace-normalized **Choi states** | **entanglement/process fidelity** (Schumacher PRA 54, 2614 (1996); Nielsen Phys. Lett. A 303, 249 (2002) for `F_avg`) | (a) leading-order (`1−F_e ≈ ‖G‖²_F/d` for coherent `V=e^{−iG}`); (b) finite-χ | Choi built from the superoperator (gauge-invariant); the intrinsic Uhlmann floor ~1e-8; use the commutator/superop-distance control for a machine-exact witness |
| Choi–Jamiołkowski trace distance | `½‖J − J'‖₁` on a seam-neighborhood reduced block | **Choi trace distance** = optimal channel distinguishability (Choi 1975; Jamiołkowski 1972; Nielsen & Chuang 2010 §9) | (a)/(b) | per-seam reduced block (global `2^{2n}` Choi infeasible); half-trace-norm ∈ [0,1] |
| Pauli-twirl distance | `½‖J(E) − J(𝒯(E))‖₁`, `𝒯(E)` = PTM off-diagonal zeroed | **the PTA / DEM approximation error** = coherence a Pauli/DEM export discards (trace distance, N&C §9; twirl-underestimate, Bravyi et al. arXiv:1710.02270; Harper) | (a) definition / (b) magnitude | reported with the **unitarity** `u(E)` coherence-of-noise scalar (Wallman et al. arXiv:1503.07865); the MODEL is never twirled — this is the metric's reference channel only |
| Multi-round comb distance | `D_comb = ½‖J(T_R^A) − J(T_R^B)‖₁` on the outcome-augmented normalized comb Choi | **quantum-comb / process-tensor distance** (Chiribella–D'Ariano–Perinotti PRA 80, 022339 (2009), arXiv:0904.4483; Pollock et al. PRA 97, 012127 (2018), arXiv:1512.00589) | (a)/(b) | `Σ_m Tr J_m = 1`; the single-round marginal-matched Markov comb is the canonical R=1 null (≡ 0 = built-in calibration) |

---

## 4. Axis-2 notion-2 multi-time record memory

Does the passive record carry the SPECIFIED classical multi-time memory, distinguishable from a
genuinely-Markov null? A **discriminability instrument, never a parameter-recovery learner** (fitting
θ from the record is the active-QNS access class, out of scope; `docs/SIMULATOR.md`).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Conditional mutual information | `I(mᵣ ; mᵣ₋₂ \| mᵣ₋₁)` (bits); `CMI = 0 ⟺ Markov-1` | **CMI Markov-order test** (Cover & Thomas 2006; Kolmogorov order, Milz et al. arXiv:1907.05807; `reading_notes/milz_when_nonmarkovian_process_classical_1907.05807.md`) | (a) `CMI=0⟺Markov-1`; measured value (b) | bits; the record's own multi-time structure, no matched-marginal subtraction (the anti-error-A property) |
| Order test | Anderson–Goodman `G² = 2N ln2 · CMI_bits`, null `~ χ²(df)` | **likelihood-ratio Markov-order test** (Anderson–Goodman; siting Kam et al. arXiv:2410.23779; `reading_notes/kam_nonmarkovian_surface_code_2410.23779.md`) | (a) null law / (c) `p<0.05` gate | Markov-1 vs Markov-2 then the order-2 rung; controls (bias-floor, true-M2 power) non-optional |
| Residual energy | `E(k) = Σ_{ℓ>k} ρ_res(ℓ)²` at the first uncontrolled lag | 1/f-vs-RTN order-relative separation (the non-forgeable power-law-tail statement is asymptotic-k) | (b) | weak at feasible `k*≈6` — report the bound; never a sharp feasible-k discriminator |
| Non-Markovianity — backflow | `N(Φ) = max ∫_{σ>0} σ(t)dt`, `σ = d/dt·½‖ρ₁−ρ₂‖₁` | **BLP trace-distance measure** (Breuer–Laine–Piilo PRL 103, 210401 (2009), arXiv:0908.0238; `reading_notes/blp_nonmarkovianity_measure_0908.0238.md`) | (a) definition / (b) value | source-layer witness; a lower bound / sufficient witness of memory |
| Non-Markovianity — CP-div breaking | `I = ∫ g(t)dt`, `g` from the intermediate-map non-CP; `D_NM = I/(I+1)` | **RHP CP-divisibility measure** (Rivas–Huelga–Plenio PRL 105, 050403 (2010), arXiv:0911.4270; review arXiv:1405.0303; `reading_notes/rhp_nonmarkovianity_measure_0911.4270.md`) | (a) definition / (b) value | **RHP is strictly finer than BLP** — report both, state which is claimed. Gaussian 1/f is CP-divisible ⇒ legitimacy is **notion-2, not notion-1** |

---

## 5. QEC operational metrics — decoder-facing, field-standard

The published QEC noise-model / decoder scores; finite-sample on shots (bootstrap CI; held-out splits
declared before fitting).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Logical error per round | `ε_d` from `F(t) ≈ A₀(1−2ε_d)^t` | **ε_d — logical error per round** (Google arXiv:2102.06132; Willow arXiv:2408.13687) | (b) | per round, not per experiment; decoder named; fit window declared (`A₀` = SPAM amplitude, **not** the DEM parity map `A`) |
| Error-suppression factor | `Λ = ε_d / ε_{d+2}` | **Λ suppression factor** (Google 2102.06132; Willow published Λ = 2.14 ± 0.02) | (b) | fitted across a distance ladder; below threshold ⇔ Λ>1; carries the drift/SPAM Λ-fit caveat (Vezvaee et al. arXiv:2510.18847) |
| Detection-event fraction | mean detector firing prob per round, per stabilizer weight | **detection-event fraction** (Google Nature 2021/2023/2025 supplements) | (b) | decoder-free; per weight class; the first-line model-vs-reference check, before any decoder claim |
| DEM edge agreement | Spitz Eq. 13 (exact) `p_ij = ½ − √(¼ − cov(x_i,x_j)/(1−2⟨x_i⊕x_j⟩))` | **p_ij correlation method** (Spitz et al. arXiv:1712.02360; Google 2102.06132) | (a) exact on the independent-edges model / (b) measured | timelike/spacelike edges split; **two-point only — blind to hyperedges** (Takou–Brown arXiv:2504.20212), state this when used as a baseline |
| Decoder-prior utility | `%ΔLER` under a frozen named decoder, model prior vs baseline prior | **%ΔLER from a model-informed prior** (Sivak et al. PRL 133, 150603, arXiv:2406.02700; Cao dMLE arXiv:2602.19722; Hockings et al. arXiv:2502.21044) | (b) | same decoder + same held-out shots per prior; baselines named; bootstrap CI. Decoder-side — **not** the interventional ΔLER; licenses no `do()` claim |

---

## References

**Distances / information theory.** Cover & Thomas (2006) *Elements of Information Theory* — TV, KL,
cross-entropy. Nielsen & Chuang (2010) §9 — trace distance = optimal distinguishability. Nielsen
(2014) arXiv:1401.4788 — `P_e = ½(1−TV)`.

**Channel / process fidelity.** Schumacher (1996) PRA 54, 2614; Nielsen (2002) Phys. Lett. A 303, 249
— entanglement/process fidelity. Choi (1975); Jamiołkowski (1972) — Choi–Jamiołkowski. Wallman et al.
(2015) arXiv:1503.07865 — unitarity. Bravyi et al. (2018) arXiv:1710.02270 — twirl underestimate.
Chiribella–D'Ariano–Perinotti (2009) arXiv:0904.4483; Pollock et al. (2018) arXiv:1512.00589 — quantum
combs / process tensor.

**Truncation / TN simulation.** Manabe–Suzuki–Darmawan (2025) arXiv:2308.08186 — MPS/TN leakage
simulation: dynamic-threshold SVD truncation, bond-dimension cost, area-law saturation, GTA >3×
LER-overestimate (精读 note in `reading_notes/`).

**Multi-time memory / non-Markovianity.** Milz et al. (2019) arXiv:1907.05807 — classical
(Kolmogorov) non-Markovianity. Kam et al. (2024) arXiv:2410.23779 — non-Markovian surface code, siting.
Breuer–Laine–Piilo (2009) arXiv:0908.0238 — BLP. Rivas–Huelga–Plenio (2010) arXiv:0911.4270; review
(2014) arXiv:1405.0303 — RHP. Quiroz et al. arXiv:2412.16092; Srivastava et al. arXiv:2510.13051 —
order/blind-spot context.

**QEC operational.** Google Quantum AI: arXiv:2102.06132 (2021); Nature s41586-022-05434-1 (2023);
arXiv:2408.13687 (Willow, 2025). Spitz et al. (2018) arXiv:1712.02360 — p_ij. Sivak et al. (2024)
arXiv:2406.02700 — decoder priors. Cao et al. (2026) arXiv:2602.19722 — dMLE (held-out NLL + %ΔLER).
Hockings et al. (2025) arXiv:2502.21044. Takou–Brown (2025) arXiv:2504.20212 — hyperedge blindness.
Vezvaee et al. (2025) arXiv:2510.18847 — Λ-fit caveat.
