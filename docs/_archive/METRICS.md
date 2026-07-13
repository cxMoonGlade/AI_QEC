# METRICS — the metric ledger

The canonical, **stable** definitions of every evaluation metric in the simulator — three ledgers:
the **B-path** (rep-code) ledger, the **identifiability** ledger, and the **hardware-data (R2)**
ledger — each with its standard field name, reference, and the convention carried with it. This
file is the contract created under the **standard-metrics hard constraint** — use the
field-standard metric for every evaluation, name it, and carry its convention. It exists so a
metric can never again be reasoned about under a wrong label (the surface-code "diamond
norm"→Bravyi-`P_L` slip).

**This file holds no run-specific numbers from our runs** (they go stale); the test suite is the
live source of truth. Frozen *published* literature bars may appear in a Convention cell as
context — marked as published, with their citation.

> **Note (2026-07-13):** the binding framing is `docs/SIMULATOR.md`. Provenance tags below to
> ADR 0001–0007, `docs/metric_results.md`, `docs/TWIN.md`, and `docs/_archive/PLAN.md` point to
> removed or archived docs (their content survives in git history / `docs/SIMULATOR.md`); the
> **metric definitions and their published references stand unchanged.** A simulator-specific
> metrics reference, sourced from the literature, is planned to supersede the twin-era framing here.

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
retro-audit and the X1/X2 status rule, 2026-06-10):

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
≈−0.22…−0.30.)

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

---

## Decoding-floor + residual-spectrum metrics (ADR 0007; `outputs/decoding_floor_*`)

Added 2026-06-17 under the forced ladder, for the syndrome-decoding **information floor** and the **Walsh
residual spectrum** (what correlation structure real syndromes carry beyond a declared bulk). **Metric-audit
outcome (the standard-metrics gate for this milestone): the substrate metrics are field-standard and MOST are
already ledgered above** — `%ΔLER` (Decoder-prior utility), Held-out syndrome NLL, Spitz `p_ij`, ε_d,
detection-event fraction, round-repeat bunching R̂, Independent-edges budget deficit, Fisher/Godambe. The only
NEW field-standard rows are the **floor** and the **parity-character spectrum** (below). The **MRG** (below) is
a rung-3 project-defined decision gate, not a figure of merit; the field-standard scoring of whether found
structure *matters* for decoding is **`%ΔLER` (Decoder-prior utility) + Held-out syndrome NLL** (both above),
scored on a **FITTED** model (a differentiable TN trained by NLL), not a preset DEM.
Finite-sample + bootstrap-CI convention (hardware regime); held-out splits declared before fitting.

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Syndrome-decoding floor (Bayes-optimal LER) | `outputs/phase0_floor_controls.py` (R=1 exact); derivation `outputs/decoding_floor_derivation.md` | **rung-2 field-standard.** Bayes error of the optimal (MAP) syndrome decoder: `LER* = ½(1 − ‖π₀P₀ − π₁P₁‖₁) = ½(1 − TV(P(s∣m0),P(s∣m1)))` at symmetric prior — the information-theoretic floor no syndrome-only decoder beats (Bayes risk: Cover & Thomas 2006; `P_e=½(1−TV)`: Nielsen arXiv:1401.4788; optimal/ML surface-code decoding context: Bravyi–Suchara–Vargo arXiv:1405.4883, DKLP quant-ph/0110143). Derivation cold-reviewed; the *model-free-floor-on-hardware* framing is the novel application, the metric itself is standard. | per-shot LER at fixed R; **exact only at R=1** (256-cell plug-in `Σ_s min(c₀,c₁)/N`, downward-biased ⇒ bias-corrected bootstrap + cross-fit bracket + dual CI); large-R = a **sandwich** (upper = best held-out decoder LER w/ Clopper–Pearson + selection correction; lower = Bhattacharyya, **vacuous at R≳3, stated**). Score = **gap-to-optimum vs a named decoder**; per-round form via ε_d (above) |
| Minimum-resolvable-gap (MRG) | `outputs/phase0_floor_controls.py` | ⚠ **project-defined / non-standard (ladder rung 3, flagged) — (c) DECISION GATE.** Bracket width [bias-corrected … cross-fit] used as the floor's resolution; gap-to-optimum < MRG ⇒ verdict UNDECIDED (fail-safe). Permitted: go/no-go resolvability gating only. FORBIDDEN as a premise, bound, or basis for a conclusion | per (basis, R); reported with the floor; pending a standard-naming pass |
| Walsh / parity-character residual spectrum | `outputs/phase3_residual_spectrum.py` | **rung-2 field-standard.** `m_S = E[(−1)^{Σ_{i∈S} s_i}]` — parity-character (Walsh–Hadamard) coefficients on the Boolean cube (standard harmonic analysis). The **|S|=2 sector IS the ledgered Spitz `p_ij`** (DEM edge agreement, above); the residual vs the marginal-matched independent model is the **connected cumulant**, and the irreducible **|S|≥3 connected (Ursell) cumulant IS the ledgered hyperedge analog** (Takou–Brown arXiv:2504.20212; connected-3-point-cumulant note above). Departure-from-bulk detected by **BH–Yekutieli FDR** (arbitrary dependence; Benjamini–Yekutieli 2001) on a shot-bootstrap residual SE. Same family as the ledgered **Independent-edges budget deficit** (`run_p10`). | per candidate set S; residual `r_ind = m_emp − Π_{i∈S}(1−2p_i)`; bulk-residual MUST use the connected cumulant (marginal-free) NOT the raw Walsh residual (the bulk's ~2× marginal miscalibration contaminates the latter); class-conditional `m_S^{(m)}` difference is the **LER-relevance axis — a necessary-not-sufficient marginal proxy** (judged via `%ΔLER` on a FITTED model, never asserted) |
### References (decoding-floor + residual-spectrum)
- Nielsen, F. (2014). *Generalized Bhattacharyya and Chernoff upper bounds on Bayes error using quasi-arithmetic means*. Pattern Recognition Letters 42, 25–34; arXiv:1401.4788 — `P_e = ½(1−TV)`.
- Bravyi, Suchara, Vargo (2014), arXiv:1405.4883; Dennis, Kitaev, Landahl, Preskill (2002), quant-ph/0110143 — optimal/ML surface-code decoding.
- Benjamini, Y. & Yekutieli, D. (2001). *The control of the false discovery rate under dependency*. Ann. Statist. 29(4), 1165–1188 — BH–Yekutieli FDR (arbitrary dependence).
- (Cover & Thomas 2006; Spitz 1712.02360; Takou–Brown 2504.20212; Sivak 2406.02700; Cao/dMLE 2602.19722 — already cited above.)

## Forward-fidelity / coupling metrics (QEC-coupling simulator; `forward/joint_lindbladian`, ADR 0008-adjacent)

Added 2026-06-26 under the forced ladder (theory-first, BEFORE the G2 gate design — the metric is the
field standard, NOT a project stand-in). For the **Axis-1 joint-Lindbladian composed-vs-joint fidelity**
(how faithfully a within-substep JOINT propagation differs from a naive composition `E_1∘E_2∘…`): the
field-standard channel-distinguishability measure.

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Composed-vs-joint channel infidelity | `forward/joint_lindbladian.composed_vs_joint_infidelity` (exact channel) + `…_infidelity_leading` (BCH leading) | **rung-1/2 field-standard.** **Process (entanglement) infidelity `1−F_e`** between two CPTP channels — `F_e` = Uhlmann fidelity of the trace-normalised **Choi states** `J = (1/d)Σ_{pq}E(\|p⟩⟨q\|)⊗\|p⟩⟨q\|` (Schumacher, *Phys. Rev. A* **54**, 2614 (1996); Nielsen, *Phys. Lett. A* **303**, 249 (2002) for the `F_avg` relation). Same Choi/process-fidelity convention as the `qutip_*_channels` gtchecks. | **Leading order (a)-exact:** for a coherent error `V=exp(−iG)`, `G=(i/2)[H_A,H_B]dt²` (Hermitian), traceless ⇒ `1−F_e ≈ Tr(G²)/d = ‖G‖²_F/d` (**/d, NOT /d²** — a v1 `/d²` doc error was caught + corrected). Avg-gate infidelity (RB-standard): `1−F_avg = d/(d+1)·(1−F_e) ≈ ‖G‖²_F/(d+1)`. Worst-case/FT: diamond norm (Kitaev) — reported only if needed. Exact-zero (commuting) control witnessed by `‖[L_A,L_B]‖_F ≤ NUMERICAL_ZERO` (structural, expm-free) + the superoperator Frobenius distance `‖S_composed−S_joint‖_F ≤ 1e-10` (the torch-c128 `matrix_exp` floor, declared (c)). The sharp tests are the **power laws** (`dt²`/`dt⁴`/`ζ²`), which are metric-constant-independent. **Choi-state computation — gauge-invariant (2026-07-04):** `J_joint`, `J_composed` are built DIRECTLY from the channel SUPEROPERATORS (`_choi_state_from_superop`; `J[a·d+p,b·d+q]=S[b·d+a,q·d+p]`), NOT from a `tol=0` Kraus decomposition. A (near-)unitary channel's lossless Kraus set carries spurious ~1e-8-amplitude roundoff operators whose Uhlmann `sqrt` amplifies representation noise to the documented ~2e-8 estimator floor; `J` is a gauge-invariant channel property, so the superop route removes that **implementation-artifact** floor (the *intrinsic* Uhlmann `sqrt`/`eigh` floor of ~1e-8 remains — for a machine-precision exact witness use the commutator/superop-distance controls above, never `1−F_e` alone). This is a computation refinement, not a redefinition: `1−F_e` and its Schumacher/Nielsen grounding are unchanged (`tests/test_joint_lindbladian.py` 11/11). |

| Multi-round process (comb) distance | `D_comb` (step-4 Tier-0 anchor, 2026-07-02) | **rung-2 field-standard extension of the ledgered `D_Choi` row to the MULTI-SLOT object.** The (B) product is an R-round process with mid-circuit outcomes — a **quantum comb / process tensor** (Chiribella–D'Ariano–Perinotti, PRA 80, 022339 (2009), arXiv:0904.4483; Pollock et al., PRA 97, 012127 (2018), arXiv:1512.00589); operational PT-Choi usage in the 精读'd `tn_decoders_process_tensor_nonmarkovian_2412.13739`. `D_comb = ½‖J(T_R^A) − J(T_R^B)‖₁` on the outcome-augmented normalized comb Choi `J = Σ_m \|m⟩⟨m\| ⊗ J_m`, slot legs = the data-qubit line; same Choi/trace-distance convention as `D_Choi`. | normalized `Σ_m Tr J_m = 1`; the single-round marginal-matched Markov comb is the canonical null (machine-matched); **R=1 vs the matched null ≡ 0 is the built-in calibration**; classical fields enter EXACTLY via Gaussian characteristic functions (component-graded closed form — (a)-class, no sampling). ⚠ 0904.4483/1512.00589 cited as the standard comb references, not full-text cached — the operational grounding used is 2412.13739 (cached, 精读). |

### References (forward-fidelity)
- Schumacher, B. (1996). *Sending entanglement through noisy quantum channels*. Phys. Rev. A 54, 2614 — entanglement (process) fidelity `F_e`.
- Nielsen, M. A. (2002). *A simple formula for the average gate fidelity of a quantum dynamical operation*. Phys. Lett. A 303, 249 — `F_avg = (d·F_e + 1)/(d+1)`.
- Kitaev, A. Yu. (1997). *Quantum computations: algorithms and error correction*. Russ. Math. Surv. 52, 1191 — diamond norm (worst-case, FT thresholds).
- Chiribella, G., D'Ariano, G. M., Perinotti, P. (2009). *Theoretical framework for quantum networks*. PRA 80, 022339; arXiv:0904.4483 — quantum combs (the multi-slot Choi object).
- Pollock, F. A. et al. (2018). *Non-Markovian quantum processes: complete framework and efficient characterization*. PRA 97, 012127; arXiv:1512.00589 — the process tensor.

---

## Source-layer non-Markovianity metrics (coupled-teacher WEDGE; ADR 0010-adjacent)

Added 2026-07-01 under the forced ladder — **rung-2 field-standard** (frontier-researched + 精读 BEFORE
use) for the coupled (correlated + non-Markovian) error teacher's **source/wedge layer**. Chosen because
the QEC-facing "coherence-sensitive ΔLER" is a self-contradictory phrase (LER is coherence-blind, per the
`tn_decoders_process_tensor_nonmarkovian_2412.13739` note + the 3 architecture reviews); the wedge is a
**LAYERED** claim — this source layer (does the process break CP-divisibility / show information backflow)
→ the channel layer (Pauli-twirl distance + unitarity + `D_Choi`/`1−F_e` vs the best Markov model, all
LEDGERED above) → the decoder layer (`%ΔLER` decoder-prior utility + held-out NLL on a PT-aware-vs-Markov
decoder on the SAME process, LEDGERED above). These two rows are the canonical non-Markovianity measures;
they QUANTIFY the wedge but are **not** by themselves decode-relevance — that is the decoder layer.

**Epistemic class.** The metric DEFINITIONS are (a) (theorem-grade functionals). A measured `N(Φ)`/`I`
value on a given process is a **measurement** (report with its convention); a *predicted* wedge magnitude
in a pre-registration is a (b) band. A nonzero source-layer wedge is NECESSARY-not-sufficient for a
decode-relevant result (the sufficiency is the decoder layer) — so a wedge value may NOT be used as a
premise for a decoding claim.

| Metric | Function | Standard name + reference | Convention |
|---|---|---|---|
| Non-Markovianity — trace-distance backflow | source/wedge layer (planned; the pilot's `\|ρ\|`-revival amplitude is its dephasing instance) | **BLP measure** `N(Φ)=max_{ρ1,2(0)} ∫_{σ>0} σ(t)dt`, `σ(t)=d/dt D(ρ1(t),ρ2(t))`, `D=½tr\|ρ1−ρ2\|` (Breuer–Laine–Piilo, PRL 103, 210401 (2009), arXiv:0908.0238; review Rivas–Huelga–Plenio, RPP 77, 094001 (2014), arXiv:1405.0303) | dimensionless (trace-distance units ∈[0,1], summed over `σ>0` intervals, Eq. 12); **max over initial pairs** — for PURE DEPHASING the optimum is the **σx eigenstates** (`a=0,\|b\|=1`) so `D(t)=`coherence factor `=exp(−Γ_R(t))` and `N(Φ)=`Σ of `\|ρ\|`-revival amplitudes (= the pilot's "true trough→peak amp", 0.024 @γ=0.15). Any observed growth is a **lower bound + sufficient witness**; model-free / tomography-friendly |
| Non-Markovianity — CP-divisibility breaking | source/wedge layer (planned; the pilot's ΔΓ dip is its dephasing instance) | **RHP measure** `I=∫₀^∞ g(t)dt`, `g(t)=lim_{ε→0+}[f_NCP(t+ε,t)−1]/ε`, `f_NCP=‖(E(t+ε,t)⊗1)\|Φ⟩⟨Φ\|‖_1` (Choi non-CP of the intermediate map); normalized `D_NM=I/(I+1)` (Rivas–Huelga–Plenio, PRL 105, 050403 (2010), arXiv:0911.4270; review arXiv:1405.0303) | dimensionless; needs the reconstructed intermediate map `E(t+ε,t)=E(t+ε,0)E(t,0)^{-1}` (invertibility caveat), reusing the ledgered `D_Choi` machinery. **PURE DEPHASING closed form** (Eq. 4): `I=−2∫_{γ(t)<0}γ(t)dt` = twice the area of the TCL rate below zero = 2× the pilot's ΔΓ dip (`γ(t)∝Γ_R'(t)=∫₀ᵗReC(τ)dτ`; 0.14 @γ=0.15). **RHP (CP-divisibility) is strictly FINER than BLP** (P-divisibility/backflow); report BOTH and state which is claimed — they coincide for the pilot's single-Lorentzian pure dephasing, can differ on the matrix-BCF / non-dephasing case |

### References (source-layer non-Markovianity)
- Breuer, H.-P., Laine, E.-M., Piilo, J. (2009). *Measure for the degree of non-Markovian behavior of quantum processes in open systems*. PRL 103, 210401; arXiv:0908.0238 — the BLP trace-distance / information-backflow measure. (精读: `docs/papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md`.)
- Rivas, Á., Huelga, S. F., Plenio, M. B. (2010). *Entanglement and non-Markovianity of quantum evolutions*. PRL 105, 050403; arXiv:0911.4270 — the RHP CP-divisibility measure. (精读: `docs/papers/reading_notes/rhp_nonmarkovianity_measure_0911.4270.md`.)
- Rivas, Á., Huelga, S. F., Plenio, M. B. (2014). *Quantum non-Markovianity: characterization, quantification and detection*. Rep. Prog. Phys. 77, 094001; arXiv:1405.0303 — the comprehensive review (BLP vs RHP relations, P- vs CP-divisibility).
