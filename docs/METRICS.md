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
| Syndrome-distribution total-variation | `½‖p − q‖₁` over the record support | **total-variation distance** (Nielsen & Chuang 2010 §9; `P_e = ½(1−TV)` Bayes link, Nielsen arXiv:1401.4788) | (a) at exact enumeration; (b) finite-sample | over the joint `(detectors, obs)`; a standard probability distance adopted as the **project's d3 certification metric** — the 2026-07-13 literature audit did not find a universal QEC full-record-TV standard; never use element-wise `max` |
| Record relative entropy | `KL(p_ref ‖ p_carrier) = H(p_ref,p_carrier) − H(p_ref) ≥ 0` | **relative entropy / KL** (Cover & Thomas 2006) | (a) population / (b) finite-sample | nats; `KL→0` iff the population record laws agree; project certification choice, not established universal QEC simulator practice |
| Held-out per-shot syndrome NLL | `−(1/N) Σ_n log p(y_n)` | **held-out negative log-likelihood** — the dMLE model-scoring objective (Cao et al. arXiv:2602.19722; population limit = cross-entropy, Cover & Thomas 2006) | (b) | only for a normalized generator of `P(record)`; decoder BCE/NLL for `P(logical|record)` is a different object; project certification choice |

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
| Per-cut discarded weight | `ε_cut = Σ_{i>χ} σ_i²`, with `‖ψ − ψ_χ‖² = ε_cut` for the stated normalized Schmidt cut | **Schmidt truncation identity** (standard; ADR 0010 constraint ledger) | (a) exact for that cut (bounds the STATE, not the LER) | per bond cut; no automatic cumulative `Σ ε_cut` record bound for nonlinear renormalized multi-step FET/PEPS updates — use a proven propagation theorem or direct paired reference |
| Truncation error (SVD) | `2-norm of the truncated singular-value vector` = `√ε_cut` | dynamic-threshold MPS/TN truncation control (Manabe–Suzuki–Darmawan arXiv:2308.08186; `reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md`) | (c) gate | bond `χ` chosen dynamically to hold it below a declared threshold (their 1e-6 rep / 1e-4 surface) |
| χ-convergence | record statistic (§1) vs `χ`, anchored to the d3 DM oracle; a `χ*` exists + monotone | **convergence-in-χ self-consistency** (the L2 no-drift test; ADR 0010 Rung 3; Manabe Fig. 6 area-law bond saturation) | (b) at d3 / (c) extrapolated | at d5/d7 this licenses only provisional engineering/reporting, never correctness or a downstream premise; drift as `χ` grows ⇒ NOT converged ⇒ STOP |
| Average bond dimension | `mean χ` per round | representation **cost proxy** (Manabe 2308.08186 Figs 5–7) | (c) | resource guard only; saturates over rounds under area law |
| Leakage / seepage rate | `L1, L2` (leaked-population growth / return) | leakage & seepage rates (Wood–Gambetta; Manabe 2308.08186 Eq. 14–15 diagnostic) | (c) diagnostic | qutrit `\|2⟩` mass; a leakage diagnostic, not a record observable (ADR 0011 Context) |
| Global cq-state trace distance | `D(ρ_RS,ρ̃_RS)=½‖ρ_RS−ρ̃_RS‖₁`, retaining the complete classical record register `R` | trace distance + data processing (Nielsen & Chuang §9; Werner et al. PRL 116, 237201 gives a global bound only for its 1D local Markov LPTN) | (a) implication when a valid global bound exists | `D≤ε ⇒ TV(P_R,P̃_R)≤ε` and fixed-decoder absolute LER error `≤ε`; rare relative LER error requires `ε≪p_L`; a final state after discarding `R` is insufficient |

**⚠ Do not gate faithfulness on local entries in this section.** Singular-value, WTG, ZMT, and FET
objectives bound a state/environment quantity under their own assumptions; they do not prove full
record or LER fidelity. The earlier statement that the coherent leakage tail has zero record content
was reopened by the 2026-07-13 literature audit. Only a valid global cq-state/process bound or the
independent d3 record ladder in §1 may license dropping it.

---

## 3. Channel / process distances — carrier certification at d3

Channel-level cross-checks of the carrier against the exact-DM / from-scratch oracle (Rung 0–1).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Process (entanglement) infidelity | `1 − F_e`, `F_e` = Uhlmann fidelity of the trace-normalized **Choi states** | **entanglement/process fidelity** (Schumacher PRA 54, 2614 (1996); Nielsen Phys. Lett. A 303, 249 (2002) for `F_avg`) | (a) leading-order (`1−F_e ≈ ‖G‖²_F/d` for coherent `V=e^{−iG}`); (b) finite-χ | Choi built from the superoperator (gauge-invariant); the intrinsic Uhlmann floor ~1e-8; use the commutator/superop-distance control for a machine-exact witness |
| Normalized-Choi-state trace distance | `½‖J − J'‖₁` on a seam-neighborhood reduced block | trace distance between outputs for the fixed maximally-entangled Choi input (Choi 1975; Jamiołkowski 1972) | (a)/(b) | project channel diagnostic/lower bound; **not** general optimal channel distinguishability, which is governed by the diamond norm; per-seam block only (global `2^{2n}` Choi infeasible) |
| Pauli-twirl distance | `½‖J(E) − J(𝒯(E))‖₁`, `𝒯(E)` = PTM off-diagonal zeroed | **the PTA / DEM approximation error** = coherence a Pauli/DEM export discards (trace distance, N&C §9; twirl-underestimate, Bravyi et al. arXiv:1710.02270; Harper) | (a) definition / (b) magnitude | reported with the **unitarity** `u(E)` coherence-of-noise scalar (Wallman et al. arXiv:1503.07865); the MODEL is never twirled — this is the metric's reference channel only |
| Outcome-augmented comb-Choi trace distance | `½‖J(T_R^A) − J(T_R^B)‖₁` on normalized comb Choi states | fixed-Choi representation diagnostic (Chiribella–D'Ariano–Perinotti PRA 80, 022339 (2009); Pollock et al. PRA 97, 012127 (2018)) | (a)/(b) | `Σ_m Tr J_m=1`; not the general optimal adaptive process-discrimination distance, which requires a strategy/comb norm over admissible testers |

---

## 4. Axis-2 notion-2 multi-time record memory

Does the passive record carry the SPECIFIED classical multi-time memory, distinguishable from a
genuinely-Markov null? A **discriminability instrument, never a parameter-recovery learner** (fitting
θ from the record is the active-QNS access class, out of scope; `docs/SIMULATOR.md`).

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Conditional mutual information | local `I(mᵣ;mᵣ₋₂\|mᵣ₋₁)`; process-wide Markov-1 requires `I(mᵣ;M_{<r-1}\|mᵣ₋₁)=0` for all relevant `r` | **conditional-independence / Markov-order test** (Cover & Thomas 2006; Milz et al. arXiv:1907.05807) | (a) for the stated full-history condition / (b) measured | the three-time quantity is only a lag-2 diagnostic and can miss dependence on earlier history; state stationarity/support assumptions and tested history depth |
| Order test | Anderson–Goodman `G²` likelihood ratio under a declared stationary finite-order chain | **finite-order Markov transition test** (Anderson–Goodman; QEC siting context Kam et al. arXiv:2410.23779) | (a) asymptotic null under regularity / (c) gate | name compared orders, degrees of freedom, sparse-cell treatment, and power controls; no finite ladder excludes every higher-order HMM |
| Residual energy | `E(k) = Σ_{ℓ>k} ρ_res(ℓ)²` at the first uncontrolled lag | project 1/f-vs-RTN order-relative diagnostic | (b) | weak at feasible `k*≈6`; never a sharp proof against every finite-order generator |

### 4a. notion-1 — distinct reduced-map divisibility and backflow criteria (not record metrics)

| Metric | Formula | Standard name + reference | Class | Convention |
|---|---|---|---|---|
| Backflow | `N(Φ)=max ∫_{σ>0}σ(t)dt`, `σ=d/dt·½‖ρ₁−ρ₂‖₁` | **BLP trace-distance measure** (Breuer–Laine–Piilo PRL 103, 210401 (2009), arXiv:0908.0238) | (a) definition / (b) value | property/witness of a reduced dynamical-map family; classical random fields can produce it (Lo Franco et al., PRA 85, 032318; Cialdi et al., PRA 100, 052104), so it is not a quantum-bath certificate |
| CP-indivisibility | `I=∫g(t)dt`, `g` from the intermediate-map Choi non-CP; `D_NM=I/(I+1)` | **RHP measure** (Rivas–Huelga–Plenio PRL 105, 050403 (2010), arXiv:0911.4270) | (a) definition / (b) value | RHP and BLP are distinct; report which is claimed. The positive-exponential-covariance **Gaussian surrogate** is CP-divisible by project algebra. Two explicitly declared free-induction lifts of the finite-RTN defaults have exact BLP backflow (`finite_rtn_exact_cpdiv_result_2026-07-13.md`), but neither lift is the production `z -> Theta` QEC channel. A stochastic source alone has no reduced-map status, and neither a diagnostic value nor record CMI transfers to the production path without a proved channel/instrument bridge |

### 4b. notion-3 — quantum process memory/backaction (active access boundary)

There is no single fixed-passive-record notion-3 metric in the current scope. Process-tensor temporal
entanglement or quantum-memory witnesses require a declared family of interventions/testers (Giarmatzi–Costa;
Taranto et al.). A `measure-all` versus `skip-intermediate-measurement` Kolmogorov/DNI statistic is itself an
instrument comparison, not one passive record, and fixed-basis violations can be produced by invasive Markovian
channels. It cannot certify quantum-bath origin. The simulator may still preserve quantum-generated mechanisms
that affect its fixed record; **physical reachability and certification of quantum origin are different claims.**
The claim-by-claim source audit is
`docs/twin_validation/notion123_taxonomy_literature_closure_2026-07-13.md`.

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
LER-overestimate (精读 note in `reading_notes/`). Evenbly (2018) PRB 98, 085155 — WTG/cycle
entropy/FET boundaries. Werner et al. (2016) PRL 116, 237201 — 1D local-Markov LPTN global trace-norm
bound. Cross-source scope audit: `docs/nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`.

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
