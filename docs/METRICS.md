# METRICS — the metric ledger

The canonical, **stable** definitions of every evaluation metric in the twin — three ledgers:
the **B-path** (rep-code) ledger, the **identifiability** ledger, and the **hardware-data (R2)**
ledger — each with its standard field name, reference, and the convention carried with it. This
file is the contract created under the **standard-metrics hard constraint** — use the
field-standard metric for every evaluation, name it, and carry its convention. It exists so a
metric can never again be reasoned about under a wrong label (the surface-code "diamond
norm"→Bravyi-`P_L` slip).

**This file holds no run-specific numbers from our runs** (they go stale). Re-recorded headline
values live, dated, in [metric_results.md](metric_results.md); the `tests/test_twin_*` suite is
the live source of truth. Frozen *published* literature bars may appear in a Convention cell as
context — marked as published, with their citation.

## The rule — metric choice is a forced ladder

**Every quantitative claim is scored by a field-standard metric, chosen by this ladder.** No rung may
be skipped and no non-standard stand-in may be used silently (the cautionary case: a surface-code score
labeled "diamond norm" that was actually Bravyi `P_L`).

1. **Use a metric in the ledger below** — by its field-standard name, reference, and convention, carried
   with every number.
2. **If no listed metric fits, research the frontier first.** Search the recent / frontier literature for
   the field-standard metric that does (as the identifiability table was added after the 2026-06-09
   literature check), then **add it to the ledger** — standard name + reference + convention — and use it.
3. **Only if none exists, create one — and flag it.** A project-defined metric is legitimate solely when
   the frontier has no standard. It must be (a) marked **project-defined / non-standard**, (b) justified,
   and (c) carried as a flagged item pending a standard-naming pass (as `B_misspec` is). A created metric
   is a debt, not a default.

**STOP condition.** About to evaluate and unsure the metric is the field standard, or you notice a
standard is being skipped → run this ladder *before* producing the number. Identifiability / numerics
claims additionally carry their evidential tier (certificate- vs numerics-grade vs flagged).

## The epistemic-status declaration (standing rule, 2026-06-10)

Every pre-registration declares, per quantitative item, which of THREE classes it belongs to —
so nothing heuristic can later promote itself to "proven" (the rule generalizes the M1/M2
retro-audit and the X1/X2 status rule, both recorded in `metric_results.md` 2026-06-10):

- **(a) exact** — a theorem, algebraic identity, or zero-tolerance check (e.g. bit-for-bit
  parity, XOR-bias product bounds, fiber-constant functional identities). Only these may serve
  as premises, definitions, or derivation steps downstream.
- **(b) prediction band** — a pre-registered falsifiable bet (fault-budget estimates, derived
  central values, band widths). Needs registration-before-run, not proof; a miss is a finding
  with its registered routing. Never citable later as an established fact.
- **(c) heuristic gate / decision rule** — thresholds, significance conventions, margins,
  eliminative-control verdicts, empirical design constants. Permitted roles: pre-registered
  go/no-go gating, tripwires, design inputs whose downstream validity is independent (state the
  independence). FORBIDDEN as a premise, definition, derivation step, error bound, or basis for
  any conclusion; a needed bound must be derived independently.

A registration item with an undeclared class defaults to (c) — the most restrictive reading.

## Conventions that apply throughout

- **Exact, not sampled.** The forward enumerates the joint `p(s, m)` exactly, so every metric below is
  its **population** value (infinite-data limit), not an empirical estimate — except where a metric is
  explicitly a finite-sample object (the calibration NLL; see below). *Scope:* this applies to the
  B-path and identifiability tables; the hardware-data section declares its own finite-sample +
  bootstrap-CI convention.
- **Units:** information quantities in **nats** (natural log). LER / ΔLER are probabilities.
- **Numerical floor:** `NUMERICAL_ZERO = 1e-12` for `log(0)` and reachable-branch masking (see
  `qec_twin.numerics`).
- **Frozen decoder:** all LER/ΔLER/regret are scored under one frozen MWPM decoder predeclared at a
  nominal physical rate; the decoder is never refit per channel.

## Ledger

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Calibration objective | `calibration.nll.joint_cross_entropy` | Born-rule observation **NLL** (the MLE objective). The *finite-sample* NLL `−Σ N(y) log p(y∣θ)` is the estimator object; the code computes its **population / infinite-data limit**, the cross-entropy `H(p_T, p_twin) = −Σ_{s,m} p_T log p_twin` (Cover & Thomas 2006). The statistical (coverage/credible) band lives in the finite↔population gap. | nats; summed over calibration contexts `C_cal(r)`; teacher mass on an `(s,m)` the twin cannot produce hits the 1e-12 floor = irreducible model-class-mismatch NLL |
| Calibration recovery | `calibration.nll.joint_kl` | **Relative entropy** `KL(p_T ‖ p_twin) = H(p_T,p_twin) − H(p_T) ≥ 0` (Cover & Thomas 2006) | nats; "`calib_KL → 0`" ⇔ the joints agree (observationally adequate, not channel-recovered) |
| Logical error rate | `knobs.intervention.logical_error_rate` (`differentiable_ler` = autograd form) | **Logical error rate (LER)** under the frozen decoder, exact over the enumerated joint (standard QEC operational metric; Fowler et al. 2012, arXiv:1208.0928) | per memory experiment; reachable branches (`p > 1e-12`) only |
| Interventional effect | ΔLER `= LER(do) − LER(base)` | channel-level `do()` effect on the LER (the manipulate capability) | held-out eval context; same intervention applied to teacher and twin |
| Knob counterfactual error | `knobs.intervention` score `knob_dler_error` (was `B_LER`) | `\|ΔLER_twin − ΔLER_teacher\|` — counterfactual-validity error of the knob | absolute, in LER units; per `do()` target + eval context |
| Observation-shift distance | `knobs.intervention` score `obs_shift_tvd` (was `B_obs`) | **total-variation distance** `½‖Δp_twin − Δp_teacher‖₁` of the `do()`-induced shift vectors (standard TV distance) | over the joint `(s,m)` support; the two shift vectors are each zero-sum |
| Window-reconstruction Choi distance | `D_Choi` (CF-WR carrier-feasibility) | **per-seam reduced-block Choi–Jamiołkowski trace distance** `½‖J_s − J'_s‖₁` between the exact reduced-channel Choi block on a seam neighborhood `s` (support ≤6q ⇒ Choi block ≤2¹² dim, feasible) and its windowed-glued reconstruction (Choi 1975; Jamiołkowski 1972; trace distance = optimal channel distinguishability, Nielsen & Chuang 2010 §9). **CF-WR amendment 1 (2026-06-14, pre-run):** computed **per-seam on reduced blocks, NOT the global 2²⁴ channel Choi** (infeasible); the global figure is the seam aggregate (= the P4 L-scaling). | normalized `J_s = (I⊗E_s)\|Ω⟩⟨Ω\|` on the seam-neighborhood support; half-trace-norm ∈ [0,1]; per-seam JRSWW+Fuchs–van de Graaf bound `D_Choi ≤ √(1 − 2^(−I_bits)) ≤ √(I_nats) = √(ln2·I_bits)`, `I(A:C\|B)` in **nats** (constant `√(I_nats)`, **not** `√(2·I_nats)`) |
| ΔLER alias band | `audit.bands.coherent_alias_floor` (certified primary); `worst_case_dler_band` (superseded failure mode) | range of ΔLER over the calibration-consistent set `{E : NLL ≤ NLL_min + slack}`. **slack selects the precise reading:** `slack → 0` = Manski **sharp identified set** (Manski 2003); `slack > 0` = Cont **model-uncertainty tolerance region** (Cont 2006). Causal `do()`-query version: Zhang & Bareinboim 2022 (arXiv:2110.05690). | band shrinks as probe richness `r` resolves the alias |
| Decision-regret | `audit.fisher_ceiling.finite_displacement_regret`; `audit.prioritization` | **minimax regret over the identified set** (Manski 2004; Stoye 2009; arXiv:2111.04926). `fiber_max` = worst-case regret over the admissible fiber; abstain-when-within-band = the non-singleton minimax-regret rule | ΔLER-suboptimality of the `do()` ranking vs the oracle, worst-case over the alias set |
| Band coverage | `prediction.drift.coverage_frequency` | frequentist **coverage probability** of the prediction band | nominal vs realized; predict-side (Gate B) |

## References

- Cover, T. & Thomas, J. (2006). *Elements of Information Theory*, 2nd ed. — cross-entropy, relative entropy (KL).
- Fowler, A. et al. (2012). *Surface codes: towards practical large-scale quantum computation*. arXiv:1208.0928 — LER as the operational QEC metric.
- Manski, C. (2003). *Partial Identification of Probability Distributions* — the identified set.
- Manski, C. (2004). *Statistical treatment rules for heterogeneous populations*, Econometrica — minimax-regret treatment choice.
- Stoye, J. (2009). *Minimax regret treatment choice with finite samples*, J. Econometrics.
- *Optimal decision rules under partial identification*. arXiv:2111.04926.
- Cont, R. (2006). *Model uncertainty and its impact on the pricing of derivative instruments*, Math. Finance 16(3) — model-uncertainty tolerance region (`docs/papers/cont2006_model_uncertainty.pdf`).
- Zhang, J. & Bareinboim, E. (2022). *Partial counterfactual identification*. arXiv:2110.05690.

## Notes

- `B_misspec` (model-class misspecification band, `audit.validity`) is a separate metric, not renamed
  here; it stays as-is pending its own standard-naming pass.
- ADRs (0003/0004/0006, GLOSSARY) retain the historical `B_LER`/`B_obs` names as dated decision records,
  each carrying a one-line pointer to this file.

---

## Identifiability metrics (`audit/fisher_ceiling`)

The W2 / cone machinery — separate from the B-path scoring layer, added under the standard-metrics
constraint after a recent-literature check (2026-06-09, prompted by the cone-result reproduction).
**Verified standard against the 2026 frontier:** Zheng et al. (arXiv:2601.22286, Feb 2026, *learnable
degrees of freedom* from syndrome data) and Ivashkov et al. (arXiv:2603.05492, Mar 2026, *ansatz-free
Lindbladian learning*) — both use the GKSL `(h, a)` coordinates and the short-time order structure this
machinery rests on.

> ⚠ **Two OUTPUTS in this table are NOT ASSUMED TRUE** (2026-06-09, user directive): the
> cone-constrained order `k` (`physical_identification_order`) and the obstruction
> `cone_obstruction_certificate` are produced by code designs **under review** — the *concept* is
> standard (refs below), but the correctness of our *current* outputs is not established. Pending
> re-validation, do not build on the `k` / certificate values. The **decision** object
> (`decision_pushforward` projection, `finite_displacement_regret`) does not depend on them.

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Learnable-DOF ceiling (Fisher corank) | `born_fisher_canonical`, `full_access_corank` | local identifiability = **Fisher-information rank** (locally identifiable iff min FIM eigenvalue > 0; Rothenberg 1971); the QEC-syndrome form is the **learnable degrees of freedom** (Zheng et al. 2601.22286; Chen et al. *learnability of Pauli noise* 2206.06362) | corank = #{eig < tol}; gauge-free GKSL `(h,a)`; machine-zero cut |
| GKSL physicality (Kossakowski PSD) | `cone_status`, `project_kossakowski_psd` | a generator is CPTP-generating **iff the Kossakowski matrix `a` is PSD** (Gorini–Kossakowski–Sudarshan 1976; Lindblad 1976); same `a_ij` as Ivashkov et al. 2603.05492 | per-location `min eig(a) ≥ −1e-12` (boundary = PSD-feasible) |
| Corrected-KL | `physical_corrected_kl` | **profile relative entropy** — KL minimized over a CPTP-feasible nuisance corrector (profile likelihood; Murphy & van der Vaart 2000) | nats; PSD-projected (certified-feasible) point; trust-regioned → local `k` |
| Identification order `k` | `physical_identification_order` | **short-time order of appearance** in the Lindbladian χ-expansion: incoherent/dissipator first-order (`χ⁽¹⁾=a`), coherent/Hamiltonian second-order (`χ⁽¹⁾=0, χ⁽²⁾≥2h²`) — Ivashkov et al. 2603.05492 Eqs 9–12; the project's Girsanov split (quadratic-variation vs drift) is this structure; coherent onset → `k≈2` | log-log slope over the t-window = **numerics-grade**; the cone-obstruction certificate is the rigorous companion |
| Cone-obstruction certificate ("physicality is a probe") | `cone_obstruction_certificate` | **CP/positivity resolves identifiability** (positivity→compressed-sensing, arXiv:1502.00536; CP constrains the GST gauge), operationalized as an **SDP-feasibility / theorem-of-alternatives** certificate (Farkas; Slater; Boyd & Vandenberghe 2004) | certificate-grade = substitution-checked witness (residual, min kernel-block eig); switches on with richness |

**Parameter-grade vs decision-grade — the off-ledger guard.** Every metric in *this* table scores
**parameter** identifiability: *can* a direction be recovered, and how hard. A direction can be
cone-resolvable / corank-reducing yet **decision-irrelevant** — the worked example is `a12i` (with
the `h_z` control), cone-classified but with **zero projection onto the `do()→ΔLER` gradient**
(Fisher σ=0, `|v·ĝ|=0` at every richness; 2026-06-09 audit), so its cone verdict carries no regret.
The **decision** claim is the regret join — `decision_pushforward` (projection onto the knob
gradient) and `finite_displacement_regret` (Manski minimax regret over the fiber; B-path ledger
above) — **never the corank / `k` / cone verdict alone**, and the `k` / cone-obstruction outputs are
themselves **not assumed true** (code under review; see the ⚠ above). The coherent onset's decision
relevance does **not** depend on them: it stands on its exact **projection** `|v·ĝ|≈0.13` and finite
**regret** ≈1.5e-2. Pinned: `test_a12i_cone_inadmissible_is_decision_irrelevant`,
`test_corank_does_not_rank_the_decision`.

**`k`-order — research note (resolves the 2026-06-09 flag).** Earlier flagged "possibly non-standard."
Resolved: the order at which a generator direction becomes observable in the short-time expansion **is**
the current-standard structure-learning primitive (Ivashkov et al. 2603.05492, Eqs 9–12) — dissipator
first-order, coherent second-order — and our coherent-onset `k≈2` reproduces their `χ⁽²⁾≥2h²`. What is
*project-specific* is the **cone-constrained ("physical / corrected") order** — the order of the
CPTP-feasible profiled KL, not the bare χ-rate — carried **numerics-grade** (the slope), with the
cone-obstruction certificate as the certificate-grade anchor. (Reproduction 2026-06-09: PSD-constrained
corrected-KL 8e-3…1.8e-1, `k≈2.2`, min Kossakowski eig at boundary; unconstrained escapes to min eig
≈−0.22…−0.30 — `dated in metric_results.md`.)

### References (identifiability)
- Gorini, Kossakowski, Sudarshan (1976); Lindblad (1976) — GKSL generator; Kossakowski-PSD = CPTP.
- Rothenberg (1971), *Identification in Parametric Models*, Econometrica — local identification via Fisher rank.
- Zheng, Chu, Chen, Manes, Lee, Zhou, Jiang (2026), *Efficient learning of logical noise from syndrome data*, arXiv:2601.22286 — learnable degrees of freedom.
- Ivashkov, Romanov, Gong, Gu, Hu, Yelin (2026), *Ansatz-Free Learning of Lindbladian Dynamics In Situ*, arXiv:2603.05492 — short-time order structure; GKSL `(h,a)`.
- *Quantum tomography protocols with positivity are compressed sensing protocols* (2015), arXiv:1502.00536 (authors: see arXiv) — positivity as an identifiability lever.
- Murphy & van der Vaart (2000), *On profile likelihood*, JASA. Boyd & Vandenberghe (2004), *Convex Optimization* — SDP feasibility / duality.

---

## Hardware-data metrics (R2 — published-dataset rungs; ADR 0007)

Added 2026-06-09 under the forced ladder — **rung 2** (frontier-standard, researched and
ledgered *before* use) for the experiment/noise-model metrics, two **finite-sample hardware
restatements** of already-ledgered B-path metrics (band coverage; Tier-0 alias band + abstain),
and one **rung-3 flagged project-defined** metric (window-closure leakage). These score the
R2-lite published-data work (ADR 0007): Google repetition-/surface-code releases (Zenodo
13273331 family), windowed exact calibration, and the decoder-prior artifact.

**Claim restriction (ADR 0007).** At R2-lite these metrics license **prediction-calibration
and decoder-prior-utility statements only** — never `do()`/counterfactual, mechanism-
attribution, Born-generation/CPTP-learning, or unscored "fits the device" adequacy claims
(PLAN.md §1.3; TWIN.md). Residual structure is reported as a misspecification *direction*
(the R2→R1 back-edge input), never an attributed mechanism.

**Population-exact does NOT apply here.** The B-path convention ("every metric is its
population value") holds only on the enumerated exact forward. On hardware shots every
metric below is a **finite-sample estimate** and carries a bootstrap CI; held-out splits
are declared before fitting.

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Logical error per round | R2 pipeline (planned) | **ε_d — logical error per round/cycle**, from the SPAM-absorbing decay fit `F(t) ≈ A₀(1−2ε_d)^t` (`A₀` = SPAM-absorbing amplitude — **not** the reserved DEM parity map `A`) (Google rep-code arXiv:2102.06132; surface code Nature s41586-022-05434-1; Willow arXiv:2408.13687) | per round, not per experiment; decoder named; fit window declared |
| Error-suppression factor | R2 pipeline (planned) | **Λ = ε_d / ε_{d+2}** (Google arXiv:2102.06132; Willow published headline Λ = 2.14 ± 0.02, arXiv:2408.13687) | fitted across a distance ladder; below threshold ⇔ Λ > 1; carries the stationarity/unitality caveat of arXiv:2510.18847 (Λ fits mislead under drift/SPAM) |
| Detection-event fraction | R2 pipeline (planned) | **average detector firing probability per round, per stabilizer weight** (Google Nature 2021/2023/2025 supplements) | decoder-free; per weight class; the first-line model-vs-device check, reported before any decoder-level claim |
| DEM edge agreement | R2 pipeline (planned) | **p_ij correlation method** — Spitz Eq. 13 (exact): `p_ij = ½ − √(¼ − cov(x_i,x_j)/(1−2⟨x_i⊕x_j⟩))`; the common `cov(x_i,x_j)/((1−2⟨x_i⟩)(1−2⟨x_j⟩))` form is its leading-order small-`p` approximation (Spitz et al. arXiv:1712.02360; Google arXiv:2102.06132) | timelike/spacelike/spacetimelike edges split; matrix-vs-matrix comparison; **two-point only — structurally blind to hyperedges** (Takou–Brown arXiv:2504.20212), state this when using it as a baseline |
| Decoder-prior utility | R2 pipeline (planned) | **%ΔLER under a frozen, named decoder from a model-informed prior vs a declared baseline prior** (Sivak et al. PRL 133, 150603; Cao et al. dMLE arXiv:2602.19722; Hockings et al. arXiv:2502.21044) | same decoder + same held-out shots for every prior; baselines named (naive calibration prior; p_ij prior); bootstrap CI. **Decoder-side comparison**: the DEM prior is the treatment arm, the decoder otherwise frozen — **not** the interventional ΔLER = LER(do)−LER(base) of the B-path ledger; licenses no `do()` claim. Published bars, baseline-tagged — dMLE up to 30.6(3)% (rep, vs correlation/pij prior) / 8.1(2)% (surface, vs RL prior; 4.9% vs pij); Sivak rep d=21 48% vs uninformative / 16% vs pij, surface d=5 10.6% vs uninformative / 3.3% vs pij |
| Band coverage (finite-sample) | hardware restatement of `prediction.drift.coverage_frequency` (`prediction/` not yet built; R2 pipeline, planned) | frequentist **coverage probability** of the forecast band, nominal vs realized, on held-out hardware slices (B-path ledger row above) | bootstrap CI; **Gate-B caveat travels**: per-window finite-shot estimation error must propagate into the forecast band (errors-in-variables / weighted regression) before any nominal-coverage claim; a pass leaves `predict` first-cut — neither Gate B nor H4 is satisfied on hardware data (ADR 0007 M5) |
| Tier-0 alias band + abstain (hardware regime) | `audit.bands.tier0_alias_band`; abstain rule: R2 pipeline (planned) | the B-path **ΔLER alias band** (Manski/Cont; ledger above) + **abstain-when-within-band** (Manski/Stoye minimax-regret rule; ledger above), restated for hardware windows | finite-sample; **indicative, not certified-covering** — the decision-regret gate (2026-06-09) showed a local/linear band under-covers at curved aliases; this caveat travels with every band number and the abstain rule inherits it |
| Held-out syndrome NLL | finite-sample form of `calibration.nll.joint_cross_entropy` | **held-out per-shot negative log-likelihood** `−(1/N) Σ_n log p(y_n)` — the finite-sample estimator whose population limit is the ledgered cross-entropy (Cover & Thomas 2006); the model-scoring objective of dMLE (arXiv:2602.19722) | per shot, nats; held-out split declared before fitting; bootstrap CI; compared on identical splits across models |
| Window-closure leakage | `hardware.windows.window_closure_audit` | ⚠ **project-defined / non-standard (ladder rung 3, flagged) — HEURISTIC RISK-AUDIT GATE, NOT A THEOREM (binding status, 2026-06-10)**: fraction of two-point correlation mass crossing a calibration-window boundary. There is NO sufficiency result "X2 ≤ threshold ⇒ bounded marginal-calibration error" — the metric is blind to higher-order cross-cut dependence. **Permitted use: pre-registered go/no-go risk gating of window selections ONLY. Forbidden use: as a premise, definition, derivation step, error bound, or basis for any conclusion.** A future cross-cut residual bound must be derived independently | threshold pre-registered before any window fit (ADR 0007 M2); reported per window size; pending a standard-naming pass |
| Local identifiability rank | `hardware.m3_report.run_p2_fisher` | **Fisher-information-matrix rank** — local identifiability ⇔ full-rank Fisher matrix (Rothenberg 1971, Econometrica 39; Cramér–Rao); `F = Jᵀ diag(1/p) J` for a categorical observation law | rank at a declared in-class point with a declared relative eigenvalue floor; eigen-split reported; a DOF *gate* run BEFORE any fit (M3 P2) |
| Independent-edges budget deficit | `hardware.m3_report.run_p10` | ⚠ **project-defined / non-standard (ladder rung 3, flagged)** — but an EXACT theorem in-project (M3 pre-registration): the XOR-bias product `1−2f_i = Π_{e∋i}(1−2p_e)` plus `−ln(1−x) ≥ x` give `Σ_{e∋i} p_e ≤ −½·ln(1−2f_i)` for ANY independent-edges DEM; since Spitz Eq. 13 is exact on that model class, a positive deficit `Σ p̂_ij − (−½ln(1−2f̂))` certifies BY CONTRADICTION that the measured pij matrix + marginals are jointly unrealizable by independent edges (shared-cause / ≥3-detector mass). Summing only the measured Δ≤1 classes is conservative (subset of the bound's left side). Built from two ledgered inputs (Spitz-exact p_ij; detection fraction); only the composite naming is ours | per detector-round; class set declared; shot bootstrap σ; floor pre-registered. **Pooled-application caveat:** B(f)=−½ln(1−2f) is convex ⇒ class pooling carries a Jensen false-positive bias ≈ ½B″·var(f) ≈ 1.2e-4 at the measured f-heterogeneity — ~2% of the 2026-06-10 measured deficits, declared |
| Round-repeat bunching ratio | `hardware.m3_report.run_p11` | ⚠ **project-defined naming (ladder rung 3, flagged)** — but an EXACT identity: for the stationary 2-state chain, `P(flip_t ∧ flip_{t+1}) / P(flip)² = (p01+p10)²/(4·p01·p10) = R` — i.e. R IS the consecutive-round pair-correlation of the flip point process, the discrete analog of photon-statistics `g⁽²⁾(0)` (hence "bunching"); ≥ 1 by AM-GM, = 1 iff p01 = p10; an i.i.d.-flip DEM is structurally pinned at 1. R is a function of the unordered pair {p01, p10} and ℤ₂-relabel invariant ⇒ FIBER-CONSTANT on the registered recoverable object (claimable without crossing the alias boundary). Standard-adjacent naming: burstiness / pair correlation — pending a standard-naming pass | plug-in Jensen positive-bias caveat travels (R̂ ≥ 1 by construction); σ from across-window spread; per basis, never pooled |

### References (hardware-data)
- Spitz, Tarasinski, Beenakker, O'Brien (2018). *Adaptive weight estimator for quantum error correction*. arXiv:1712.02360 — the p_ij method.
- Google Quantum AI (2021). *Exponential suppression of bit or phase errors with cyclic error correction*. Nature; arXiv:2102.06132 — ε_d, Λ, p_ij in practice.
- Google Quantum AI (2023). *Suppressing quantum errors by scaling a surface code logical qubit*. Nature s41586-022-05434-1.
- Google Quantum AI (2025). *Quantum error correction below the surface code threshold*. Nature s41586-024-08449-y; arXiv:2408.13687 — Willow; the released datasets.
- Sivak et al. (2024). *Optimization of decoder priors for accurate quantum error correction*. PRL 133, 150603; arXiv:2406.02700.
- Cao, Feng, Ye, Pan (2026). *Differentiable maximum likelihood noise estimation for quantum error correction*. arXiv:2602.19722 — held-out syndrome NLL + %ΔLER as the scoring pair; the closest prior art.
- Hockings, Doherty, Harper (2025). *Improving error suppression with noise-aware decoding*. arXiv:2502.21044 — prior quality compounds with distance.
- Takou & Brown (2025). *Estimating decoding graphs and hypergraphs of memory QEC experiments*. arXiv:2504.20212 — p_ij's hyperedge blindness (two-point edges largely suffice for rep/surface codes under bare-ancilla extraction, per the same paper).
- Vezvaee et al. (2025). *Surface code scaling on heavy-hex superconducting quantum processors*. arXiv:2510.18847 — the Λ-fit stationarity caveat.

---

## d3 white-box recover metrics (single-window composite likelihood; ADR 0007 / `whitebox/d3_whitebox_recover_design.md`)

Added 2026-06-15 under the forced ladder, **up front at the design/pre-registration stage** (before
any d3 result), for the d3 single-window white-box recover. **(v5 objective re-thread, 2026-06-16:** the
d3 forward is the **syndrome-conditioned multi-round detector-record likelihood** `P_θ(record)` on real
`detection_events.b8` — the earlier unconditional single-round / syndrome-averaged-stationary object was
degenerate for the unital SI1000 prior (`ρ_ss=I/16` exactly, Fisher rank 1; GPU-reproduced + reviewed,
now the negative control). The metrics below are **UNCHANGED in standardness** — `rank(H)` of a
multi-round record likelihood is the same Rothenberg-1971 FIM object, just over the record space; the
composite is now per-window over the multi-round record, not the single-round syndrome.) The fit
maximises a **per-window composite likelihood** over the multi-round detector record with **Godambe
(sandwich) standard errors**. **Most scores REUSE rows already above** and are not re-listed: held-out
**detector-record** NLL (finite-sample `calibration.nll.joint_cross_entropy`, now over the multi-round
record); KL / TV; Choi/trace distance; **Fisher-information rank** (`hardware.m3_report.run_p2_fisher` /
identifiability table; Rothenberg 1971); **detection-event fraction** (per-round, on the detector
record); **DEM p_ij** = the within-window 2-body **+ across-round** structure (Spitz 1712.02360 — the
across-round form is native to the multi-round record); **round-repeat bunching ratio R̂** (`run_p11`,
already ⚠ rung-3 — the d3 design's *within-window* R̂ is this metric, validated by a trajectory forward;
the **long-range** R̂ is out of d3 scope, → the d7 black-box). New rows:

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Composite (block-marginal) likelihood | the d3 recover FIT objective | **composite / pseudo-likelihood** `ℓ(θ) = Σ_j w_j log P_θ(record_j)` over the per-window multi-round detector records (Lindsay 1988; Varin, Reid & Firth 2011) — a consistent M-estimator when the per-window records are jointly informative about θ | `w_j ≡ 1` (all-blocks composite); each `P_θ(record_j)` is the EXACT dense-oracle R-round record-conditioned likelihood (project→renormalize→reset per round, log-domain); held-out, nats/shot/window; population limit = the ledgered cross-entropy NLL applied per window. **Captures within-window correlation only**; long-range correlation (R̂) is structurally outside it (= the independent-edges-DEM boundary) |
| Composite-likelihood identifiability + bands | composite Fisher `H` + Godambe sandwich `G = H J⁻¹ H` | **Godambe (sandwich) information** for the composite-likelihood estimator (Godambe 1960; Varin-Reid-Firth 2011 §4); identifiability = rank/null of `H` (Fisher-rank standard, Rothenberg 1971) | `H = Σ_j E_{record_j}[(∂_θ log P_θ(record_j))(∂_θ log P_θ(record_j))^T]` (composite sensitivity over the multi-round record; exact-enumerable at small R, Monte-Carlo at R=90); `J` = inter-block variability via block-bootstrap; **bands use `G`, NOT `H⁻¹`** (a pseudo-likelihood loses efficiency, `H⁻¹` mis-sizes them); `rank(H_composite) ≤ rank(H_joint)` ⇒ the alias ledger is a **conservative sufficiency lower bound**; until `J` is estimated, band widths are tagged **(c)-heuristic** |
| Coherence budget = **Pauli-twirl distance** (+ unitarity) | `forward.window_diagnostics` (twirl-distance; the off-diagonal-PTM mass is now a deprecated internal proxy) | **rung-2 field-standard** (switched 2026-06-15 from the rung-3 off-diagonal-mass proxy). The **Pauli-twirl distance** `½‖J(E) − J(T(E))‖₁` — the Choi trace distance between the channel `E` and its Pauli-twirl `T(E)` (the PTM with off-diagonal zeroed) — is EXACTLY the coherence a Pauli/DEM export discards (the PTA approximation error; trace distance = optimal distinguishability, Nielsen & Chuang 2010 §9; PTA = Harper 2605.29514; **reuses the ledgered `D_Choi` machinery**). Reported alongside the **unitarity** `u(E)` scalar coherence-of-noise measure (Wallman et al. 2015). The earlier off-diagonal Frobenius mass is the Hilbert–Schmidt norm of the same `E − T(E)` difference — a non-operational proxy, **replaced** by this trace-norm/operational standard. | per-mechanism + total; complex128; `T(E)` = PTM off-diagonal zeroed; the d3 (b)-prediction is "small" (Darmawan); the twirl here is only the metric's reference channel (the MODEL is never twirled — correction 2). **Forbidden as a premise / derivation basis.** Mainline `window_diagnostics` impl of trace-distance/unitarity is a build / commit-gate item |

**Verification-vs-claim metric note (binding, from the adversarial-self-verification lesson).** The
A-vs-B forward cross-check (`outputs/d3_born_crosscheck.py`) reports the **total-variation distance**
`½‖A − B‖₁` (the field-standard distance between the two distributions) as the primary agreement
metric, with `max|A−B|` (L∞) kept only as a strict machine-agreement diagnostic (two INDEPENDENT
computations of the SAME `P_θ(σ)`). Comparing DISTINCT distributions (model vs data, model vs baseline)
always uses the ledgered **NLL / KL / TV** — never the element-wise max (that masked the 9q-instrument's
14.4 % data-trace-distance failure). The structure-residual's 3-body term is the **connected 3-point
cumulant** (standard; hyperedge analog per Takou–Brown 2504.20212, ledgered).

### References (d3 recover)
- Lindsay, B.G. (1988). *Composite likelihood methods*. Contemporary Mathematics 80, 221–239 — the foundational composite/pseudo-likelihood reference.
- Varin, C., Reid, N., Firth, D. (2011). *An overview of composite likelihood methods*. Statistica Sinica 21, 5–42 — the standard review (consistency, Godambe sandwich §4).
- Godambe, V.P. (1960). *An optimum property of regular maximum likelihood estimation*. Ann. Math. Statist. 31, 1208–1211 — Godambe (sandwich) information / estimating equations.
- Greenbaum, D. (2015). *Introduction to quantum gate set tomography*. arXiv:1509.02921 — the Pauli-transfer-matrix representation.
- Wallman, Granade, Harper, Flammia (2015). *Estimating the coherence of noise*. New J. Phys. 17, 113020; arXiv:1503.07865 — unitarity, the frontier-standard coherence-of-noise measure.
