# Non-Markovian coupling source layer — constraint ledger (pre-build, mandatory)

**Status:** the `docs/FAITHFULNESS_PROTOCOL.md` rule-II deliverable, written BEFORE any source-layer code.
Companion to `full_error_coupling_prereg.md` (which fixes the strategy §0, the wedge metric §0.2, and the
P1–P4 predictions §5.1). This ledger lists every physical theorem the explicit non-Markovian source
model MUST satisfy, a falsifying test for each, and the INDEPENDENT ground truth each is checked against
(never the model's own oracle — the root cause of every toy we hit was circular verification).

**What is being built (scope).** An explicit non-Markovian noise SOURCE carried as a dynamical degree of
freedom (NOT a non-negative Lindblad rate — that is Markovian by construction and reproduces the owned
QMCtwin class, §0.1 of the prereg). **Primary-source pin:** QMCtwin (arXiv:2606.19848) frames its
REPORTED simulations in a non-negative Markovian rate model (verified against the arXiv source,
2026-06-26) — the primary-source support for "an explicit non-Markovian source is the unowned wedge":
- a single random-telegraph fluctuator (RTN/TLS) — exactly solvable, the anchor;
- a colored 1/f process `S(f) ∝ 1/f` — built as a sum of RTNs or an explicit construction;
- one shared draw fed into every co-modulated parameter map (the axis-2 coupling).

**Epistemic frame (`METRICS.md`):** the RTN closed form + CP-divisibility definitions + the
motional-narrowing limit are **(a) exact** (the only class usable as a premise / positive control). The
P1–P4 magnitudes are **(b) prediction bands**. The fluctuator-count / geometry cuts are **(c)
decisions**. Undeclared ⇒ (c).

---

## A. Constraint ledger (theorem → falsifying test → INDEPENDENT ground truth)

| # | Physical constraint the model MUST satisfy | Falsifying test (must be able to FAIL) | Independent ground truth (NOT the model's own sim) |
|---|---|---|---|
| **C1 — CPTP at all times** | The reduced qubit channel `E(t)` is CPTP for every `t`, even when NOT CP-divisible (non-Markovian ≠ non-physical). | Choi matrix PSD (min eigenvalue ≥ −NUMERICAL_ZERO) + trace-preservation at every `t` on the grid. | Choi/Jamiołkowski theorem (closed-form PSD test). |
| **C2 — RTN exact coherence** | Single telegraph: dephasing coherence `⟨e^{iφ(t)}⟩` matches the EXACT RTN result `L(t)=e^{-γt}[cosh(μt)+(γ/μ)sinh(μt)]`, `μ=√(γ²−v²)` (and the oscillatory branch `v>γ`). | Built coherence vs the closed form over a `v/γ` sweep across the `v=γ` branch change; assert ≤1e-9. | The Anderson–Kubo / RTN analytic solution (textbook closed form), derived independently. |
| **C3 — motional-narrowing → Markovian (POSITIVE CONTROL)** | Fast/weak limit `v ≪ γ_sw`: dynamics reduce to pure-exponential dephasing `Γ=v²/(2γ_sw)`, RHP=0, recovering the non-negative-Markovian baseline EXACTLY. | Sweep `γ_sw→∞`: assert RHP measure → 0 AND coherence → `exp(−v²t/(2γ_sw))`. If non-Markovianity persists in the fast limit, the model is BROKEN. | The motional-narrowing closed form `Γ=v²/(2γ_sw)` (independent `v≪γ_sw` limit of C2). |
| **C4 — CP-divisibility detector is sound** | The RHP (and BLP) non-Markovianity measure reads EXACTLY 0 on any genuinely Markovian (non-negative-rate) channel and >0 only in the underdamped branch `v>γ_sw`. | POSITIVE CONTROL: feed a known Markovian channel (a plain `D[√Γ n]` Lindblad) → measure MUST read 0. NEGATIVE-side: feed slow RTN (`v>γ_sw`) → MUST read >0 at the predicted crossover (P1). | RHP/BLP definitions applied to an analytically-Markovian channel (independent of the source sim). |
| **C5 — fair baseline = the STRONGEST Markovian/CP-divisible competitor (REVISED 2026-06-26 after red-team)** | ⚠ The first build's i.i.d. baseline was a STRAWMAN: it measured classical round-CORRELATION (a Markov-1 model recovered ~50% of the "wedge", Markov-k most of it), NOT non-Markovianity — correlation ≠ non-Markovianity. **Observation distribution (PRIMARY) = a COHERENCE probe** (Ramsey/echo fringe `P(+|t)=½(1+Re L(t))` over a grid of free-evolution `t`) — the ONLY channel where non-Markovianity is unforgeable. **Baseline = the best-fit CP-divisible model = ANY MONOTONE-`|L(t)|`** (multi-exponential / isotonic-regression / Markov-k on the discretized fringe — the strongest Markovian competitor, fits any monotone decay), max-likelihood on the coherence-NLL (ADR 0003). The wedge = the IRREDUCIBLE gap a monotone model leaves at a `|L|` REVIVAL. The syndrome round-correlation result (if reported) is a SECONDARY classical result and MUST be scored vs Markov-k (NOT i.i.d.), labeled "classical correlation," not the non-Markovian contribution. **NO-TOY-BASELINE rule (2026-06-26): the wedge is meaningless against a weak baseline.** The baseline = the THEOREM-BACKED SUPREMUM over all CP-divisible dephasing (the best monotone-non-increasing positive `\|L\|`, via `γ_φ≥0 ⟺ \|L\| monotone-positive` — beating it ⇒ beating QMCtwin's entire non-negative-Markovian class) AND a panel of NAMED field-standard Markovian models declared per the baseline discipline: exponential-T2 `e^{−t/T2}`, Gaussian-T2 `e^{−(t/T2)²}`, Bloch-Redfield / time-local-rate Lindblad. The wedge is reported vs the STRONGEST (lowest-NLL) of all of them. A baseline that has NOT converged to its own optimum is an artificially-weak (toy) baseline and is REJECTED. | (i) EVERY baseline is at its genuine NLL optimum (assert convergence: `nll@opt ≤ nll@(1±ε)·params`); a non-converged baseline = toy = FAIL; (ii) the supremum monotone-`\|L\|` fit AND each named standard model are reported, wedge vs the strongest; (iii) the wedge's source is the revival (non-monotone `\|L\|`), cross-checked: no revival ⇒ no wedge; (iv) Markov-k-along-t is NOT a coherence baseline (it is the secondary classical syndrome result only). | The CP-divisibility theorem: any CP-divisible dephasing has `\|L(t)\|=exp(−∫γ_φ ds)`, `γ_φ≥0` ⇒ `\|L\|` MONOTONE; a non-monotone `\|L\|` (revival) is non-Markovian BY DEFINITION (independent of any fit). The monotone-`\|L\|` supremum bounds EVERY Markovian model from below in NLL. |
| **C6 — 1/f spectrum (ANALYTIC target first, then sampling error)** | The colored process is a log-spaced sum-of-RTNs with the CLOSED-FORM spectrum `S(ω)=Σ_k v_k²·(4γ_k)/((2γ_k)²+ω²)` (sum of Lorentzians) → `∝1/f` over the band BY CONSTRUCTION. The gate is NOT a bare slope on one finite sample (noise-dominated → false pass/fail). | Two-step: (1) confirm the ANALYTIC target's slope ≈ −1 over the decade band (deterministic, from the `{v_k,γ_k}` grid); (2) the generator's empirical Welch PSD must match the ANALYTIC sum-of-Lorentzians within the finite-sample Welch/MC confidence band (χ²-per-bin); a deviation beyond the MC band is a generator bug, NOT a 1/f-slope failure. | The closed-form sum-of-Lorentzians spectrum (Dutta–Horn) computed from the `{v_k,γ_k}` grid — the analytic target precedes sampling; the generator's sampling error is measured against it within the MC band. |
| **C7 — telegraph statistics** | RTN autocorrelation `C(τ)=v²·e^{−2γ_sw τ}`; one-fluctuator amplitude statistics are BIMODAL (two-valued), not Gaussian. | Empirical autocorr of the generated source vs the analytic `e^{−2γ_sw τ}` (≤ MC band); histogram bimodality test (single TLS). | The RTN autocorrelation closed form. |
| **C8a — source latent autocorr (EXACT)** | The generated source's LATENT autocorrelation is exactly `⟨ξ(0)ξ(τ)⟩=e^{−2γ_sw τ}` (RTN). This is an exact property of the source, independent of any readout. | Empirical latent autocorr of the generated source vs `e^{−2γ_sw τ}` within the MC band; assert. | The RTN autocorr closed form (C7). |
| **C8b — OBSERVABLE cross-cycle correlation (PREDICTION BAND, class b)** | The OBSERVABLE syndrome/error round-to-round correlation TRACKS the source autocorr but is NOT equal to it: `obs-corr ≈ e^{−2γ_sw t_cycle}` holds only under a LINEAR/MONOTONE observation map; the true syndrome/readout map is nonlinear, so this is a class-(b) band around the source autocorr, never an equality. Emergent (rate-driven), COLLAPSING to 0 in the fast limit. | Slow source → observable round-corr lands in the predicted band around the C8a source autocorr; NEGATIVE CONTROL: fast source → observable round-corr → 0 (the TLF push passed this). A gap between observable-corr and source-autocorr is a FINDING about the observation map, NOT a fail. | C8a source autocorr at `t_cycle` as the band CENTER; the observation-map nonlinearity sets the band width (reported, not assumed). |
| **C9 — conditional coverage, ISOLATION-RESPECTING (P4, decision-level)** | A learner/DEM calibrated on the source's MARGINAL rate is conditionally miscalibrated given the source state. The source-resolved twin conditions on its POSTERIOR over the source from **learner-visible history ONLY** — it NEVER consumes the true latent. **Isolation-correct claim** (do NOT demand near-nominal on the true-state audit — matching the true-state-conditioned rate requires the CURRENT latent, which isolation forbids; the history-only twin's residual is the irreducible FILTERING LAG, shrinking as the source slows / the posterior sharpens). | (i) baseline true-state dev ≫ 0 (conditionally miscalibrated); (ii) the history-twin STRICTLY improves it: `dev_twin < dev_baseline`; (iii) **decision-relevant** = SELF-CALIBRATION in the twin's OWN predictive terms (reliability: when it predicts `p`, the realized rate ≈ `p`) — the history-twin passes, the constant-marginal baseline fails conditionally; (iv) a latent-PEEKING cheat-twin (evaluator-only) reaches near-nominal on the true-state audit → proves headroom AND that the audit is informative; (v) the isolation assertion (twin invariant to SCRAMBLING the latent; a peeker is detectably different & better). NOT "twin ≈ nominal on the true-state audit". | Source-resolved exact conditional error rate (evaluator-only) + the twin's own posterior-predictive reliability; the twin's INPUT is strictly learner-visible history, never the latent. |
| **C10 — motional-narrowing COLLAPSE (the P1↔wedge link — HARD GATE, added 2026-06-26; refined after the v3 run)** | The coherence wedge (C5) MUST be CAUSED by non-Markovianity, not by parametrization. **Load-bearing claim = the COLLAPSE:** wedge ≈ 0 on the Markovian side `v<γ_sw` (monotone `|L|`, a CP-divisible baseline fits exactly) AND wedge > 0 & monotone-rising on the non-Markovian side. **The turn-on is at the OBSERVABLE-revival threshold `v*≳γ_sw`, NOT the infinitesimal RHP onset** — physically, the `|L|`-revival amplitude is `~e^{−γ_sw·t_revival}`-suppressed near the crossover (e.g. at `v/γ_sw=1.25` the first revival is damped to ~3e-4), so a finite-data NLL wedge is UNobservable in the narrow band `γ_sw<v<v*` even though RHP (sensitive to infinitesimal negativity) is already >0 there. This `v*` gap is a REPORTED finding (the wedge detects OBSERVABLE revival, RHP detects any revival), not a failure. | Sweep `v/γ_sw`: (i) assert wedge ≈ 0 (within MC floor) for `v≤γ_sw` — THE load-bearing collapse; (ii) wedge > 0 and monotone-rising for `v≥v*` (the observable-revival region); (iii) **the wedge magnitude MONOTONE-non-decreasing in the `|L|`-revival amplitude across the sweep** (grid-independent, threshold-free; Spearman reported) — the ill-posed "co-located within one grid step" was retired (two different-sensitivity floors, grid-dependent); (iv) **NEGATIVE CONTROL (the real teeth, added after re-adjudication): route genuinely Markovian / monotone-`|L|` sources — incl. OUT-OF-FAMILY Gaussian/exp dephasing — through the SAME machinery and assert wedge ≤ +floor (NO false positive).** REPORT `v*` + the disclosed caveats (next cell). **If the wedge does NOT collapse for `v<γ_sw`, OR a Markovian source produces a positive wedge, STOP and retract.** **DISCLOSED CAVEATS (honest limits, independently confirmed): (a) operating regime is `v≳1.8γ_sw` NOT `v>γ_sw` — `γ_sw<v≲1.8γ_sw` is non-Markovian (RHP>0) but wedge-unobservable (exponential revival suppression); (b) the collapse gate is ONE-SIDED (false-positive guard only); (c) wedge magnitude is shot-count-dependent (qualitative detector, +776@40k→+3822@200k).** | The CP-divisibility crossover (C4 RHP) AND the analytic `|L|`-revival amplitude AND a Markovian-source negative control (out-of-family monotone-`|L|` → wedge≤0) — all independent of the wedge. |

---

## B. Declared + bounded simplifications (rule III — every one bounded, unbounded ⇒ STOP)

| # | Simplification | Epistemic class | Bound / control |
|---|---|---|---|
| S1 | **Finite fluctuator count** approximating 1/f (sum of `N` RTNs, log-spaced `γ_sw`). | (c) design | bound the PSD error vs ideal 1/f over the band (C6); report `N` and the residual; increase `N` until the wedge metrics are stable. |
| S2a | **RTN = classical pure-dephasing model** (the source modulates frequency only; no qubit↔TLS energy exchange). | (a) exact | the C2 closed form is EXACT for this model — no bound needed (it IS the model, not an approximation of it). |
| S2b | **Not modeling a quantum TLS (T1-exchange / energy relaxation)** in v1. | (c) design/scope | a SCOPE decision, not an approximation of the dephasing model: the contribution targets non-Markovian DEPHASING. A quantum TLS (T1-exchange) is a SEPARATE source with its own ledger row when added; its omission changes coverage, not the fidelity of S2a's dephasing channel. |
| S3 | **Coupling geometry** (which qubits see which fluctuator; shared vs independent). | (c) | swept, not frozen: a panel {independent, shared-pair, shared-neighbourhood}; the shared case is the spatial-correlation lever, reported with sensitivity. |
| S4 | **Stationarity** (constant `γ_sw`, `v` over the experiment). | (c) | declared; drift of the fluctuator parameters themselves (1/f of 1/f) is out of scope for v1, flagged. |

---

## C. Build gates (a deliverable is "done" only when)

1. **C1–C4 pass** (CPTP + RTN exact + motional-narrowing positive control + a SOUND CP-divisibility
   detector with its Markovian-reads-0 positive control). These are the (a)-exact foundations — they
   gate everything; a failure here is a stop, not a band-widen.
2. **C5 holds** (the wedge is on a COHERENCE observable vs the STRONGEST monotone-`|L|`/CP-divisible
   baseline — multi-exp/isotonic/Markov-k, NOT i.i.d. — and survives vs Markov-k; the syndrome
   round-correlation, if reported, is a SECONDARY classical result scored vs Markov-k).
2b. **C10 holds** (the wedge COLLAPSES in the motional-narrowing limit `v<γ_sw` and turns on at `v=γ_sw`,
   co-located with the C4 RHP crossover — the proof the wedge measures non-Markovianity; non-collapse ⇒ STOP).
3. **C6, C7, C8a** confirm the analytic-target-validated 1/f spectrum, telegraph statistics, and the
   EXACT source latent autocorr.
4. **The P1–P3 prediction bands** (prereg §5.1) are measured against C2/C3/C7/C8a ground truth; the
   OBSERVABLE round-corr is the C8b prediction band (not an equality); a miss is reported as a finding
   (not silently re-fit).
5. **C9 / P4** the decision-level conditional-coverage signature is demonstrated source-resolved vs
   marginal-Markovian.
6. **Process discipline:** ≥3 disjoint-ownership builders + a separate un-led reviewer (heavy task);
   every run a committed script (asserts + printed evidence + flushed + `__main__` guard); GPU-only,
   serialized, no concurrent heavy jobs; mainline (`src/`) untouched + commit-gated.

**Red-team (rule II close):** a from-scratch adversarial pass must try to make each of C1–C10 FAIL —
ESPECIALLY C5/C10 (is the "wedge" actually non-Markovianity, or just round-correlation a Markov-k model
captures? does it collapse in the motional-narrowing limit? — the 2026-06-26 red-team caught exactly this
when the wedge was on syndromes vs an i.i.d. strawman) — and C3 (does a subtle bug keep
"non-Markovianity" alive in the fast limit?) and C4 (does the detector read >0 on a genuinely Markovian
channel = a false wedge?). A wedge that survives only because
the detector is biased is the toy this ledger exists to prevent.
