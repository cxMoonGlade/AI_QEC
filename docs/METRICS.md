# METRICS — the B-path metric ledger

The canonical, **stable** definitions of every evaluation metric in the rep-code (B-path) twin:
its standard field name, reference, and the convention carried with it. This file is the contract
created under the **standard-metrics hard constraint** — use the field-standard metric for every
evaluation, name it, and carry its convention. It exists so a metric can never again be reasoned
about under a wrong label (the surface-code "diamond norm"→Bravyi-`P_L` slip).

**This file holds no run-specific numbers** (they go stale). Re-recorded headline values live, dated,
in [metric_results.md](metric_results.md); the `tests/test_twin_*` suite is the live source of truth.

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

## Conventions that apply throughout

- **Exact, not sampled.** The forward enumerates the joint `p(s, m)` exactly, so every metric below is
  its **population** value (infinite-data limit), not an empirical estimate — except where a metric is
  explicitly a finite-sample object (the calibration NLL; see below).
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
