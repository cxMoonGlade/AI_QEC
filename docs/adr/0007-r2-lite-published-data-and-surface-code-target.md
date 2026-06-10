# ADR 0007: Pull the Published-Data Rung Forward (R2-lite), Declare the Surface-Code Target, Ledger the Industry Metrics

## Status

Accepted (2026-06-09). Amends the rung ladder of [`plan2.md`](../plan2.md) §3 (R2 splits
into **R2-lite / R2-full**) and **schedules** the `forward/scalable` carrier feasibility
study (it does not choose the carrier — that is ADR 0008's job). Extends
[`METRICS.md`](../METRICS.md) with the hardware-data ledger. Does **not** move the claim
boundary (PLAN.md §1.3, TWIN.md §claims) and does **not** reverse the decision-regret
gate's verdict — the Claim-B band engine stays deferred exactly as banked
(`tests/test_decision_regret_gate.py`, `metric_results.md` 2026-06-09).

## Context

Five facts force a sequencing decision now.

1. **The goal is a tool; the contribution is the twin.** The project's end goal
   (recorded 2026-06-09) is a practical digital-twin toolkit with QEC-industry impact.
   Its priority claim is the **composition** — recover + understand + manipulate +
   predict over one CPTP object, with honest alias bands and controlled-`do()`
   counterfactual validation — not any single ingredient. Recorded stance: being
   preempted on individual ingredients (syndrome-only fitting, beyond-Pauli
   characterization, decoder priors — dMLE arXiv:2602.19722, ACES-decoding
   arXiv:2502.21044, and Takou–Brown arXiv:2504.20212 / 2510.23797 are converging on
   that niche) does **not** invalidate the program, and racing them point-by-point is
   explicitly not the strategy. The race the twin can win is the one nobody else is
   running: calibrated uncertainty + abstention + counterfactual prioritization on one
   object. Corollary (user directive, 2026-06-09): **novelty positions are sequenced,
   not ceded** — every deferred item in this ADR (the Claim-B band engine, the composed
   prioritization engine, the surface-code twin) remains a claimed ambition with a
   recorded re-open trigger; the current cut (H2 + R2-lite M1–M5) completes first.

2. **The flagship datasets are local, and one fits the exact backend today.** All four
   Google releases (Zenodo 13273331 family, CC-BY, stim-native `.stim`/`.dem`/`.b8`) are
   downloaded under `/home/cx/Document/`: `google_72Q_repetition_code_d29` (the d=29
   chain, enormous shot volume, acquired as a sequentially indexed sample series —
   100 samples per basis; the recalibrate-every-4-runs protocol belongs to the 72Q
   *surface-code* stability set, whose set2 release notes deliberately mixed
   calibration freshness),
   `google_72Q_surface_code_d3_d5_set1/2`, `google_105Q_surface_code_d3_d5_d7`. The
   d=29 repetition-code chain is quasi-1D and gate-local: sliding windows of 5 data +
   6 measure qubits (11q; up to 7+8 = 15q) sit **inside** the §1.1b exact window — real
   flagship data is reachable **without** `forward/scalable`. The surface-code releases
   are not: rotated d=3 is already 17q (> ~15q), d=5 is 49q, d=7 is 97–101q.

3. **The declared target is the surface code at d=5–7, not the repetition code.**
   (User decision, 2026-06-09.) Rep-code windows are an **entry rung only**. A full
   d=5/d=7 surface-code twin strictly requires the scalable carrier — the >15q wall
   (ADR 0006 Decision 4) is no longer a hypothetical to be "confronted later"; it is
   the declared destination, so the carrier moves onto the critical path.

4. **The plan-as-written path to any real-data output protects claims R2-lite does not
   make.** plan2 §3 orders R2 behind the taxonomy gate (needs H2+H3+H4 built) and the
   composed decision-regret gate (needs `predict`, an empty placeholder). Those gates
   exist to protect `do()` / attribution / ranking claims. Four of the five R2-lite
   milestones (M1–M4) make none of those claims, so holding them behind those gates
   buys no epistemic safety; the one genuine intersection is the drift leg (M5), which
   touches what Gate B protects and is scoped accordingly (Decision 4, M5). Early
   contact with real data is what the load-bearing back-edge (plan2 §3) names R2's
   most valuable output — and what this ADR strengthens into the prioritizer of
   remaining HARDEN work (Decision 1).

5. **Field currency and the unowned seam (2026-06-09 review, web-verified).**
   Noise-model quality on real QEC data is scored by: held-out syndrome NLL, pij-matrix
   / detection-event-fraction agreement, and %ΔLER under a frozen named decoder
   (published bars, baseline-tagged: dMLE up to 30.6% rep-code vs the correlation/pij
   prior, 8.1% surface-code vs the RL prior — 4.9% vs pij; Sivak et al. PRL 133,
   150603: rep d=21 48% vs uninformative / 16% vs pij, surface d=5 10.6% vs
   uninformative / 3.3% vs pij; AlphaQubit ~30% fewer logical errors than correlated
   matching). The ecosystem seam `raw .b8 → calibrated DEM (+ uncertainty) → any
   stim-DEM decoder` is today per-paper scripts; **no existing tool emits uncertainty
   bands, abstain flags, or CPTP-capable priors** — exactly the twin's differentiators.

## Decision

**1. Split R2 into R2-lite and R2-full; enter R2-lite now, in parallel with H2.**

- **R2-lite — allowed claims:** prediction-calibration and decoder-prior utility only,
  scored exclusively by the METRICS.md ledger (the hardware-data section, including its
  finite-sample restatements of the band-coverage and Tier-0-band/abstain rows):
  held-out per-shot syndrome NLL vs declared baselines; pij / detection-fraction
  agreement; %ΔLER under a frozen, named decoder (pymatching) vs the naive-calibration
  and pij priors; sample-indexed drift trajectories with finite-sample band coverage
  (Gate-B-scoped — see M5); per-window Tier-0 bands with the abstain-when-within-band
  rule where richness was not earned, reported **indicative, not certified-covering**
  (the local-band under-coverage caveat travels with every band number).
- **R2-lite — forbidden claims (R2's own restrictions plus the §1.3 boundary):** any
  `do()` / counterfactual / intervention claim on hardware; any mechanism attribution
  ("this residual *is* leakage"); any Born-generation / CPTP-learning /
  physical-mechanism claim; any unscored "fits the device" adequacy language. Residual
  structure is reported as a **misspecification direction** (back-edge input), never an
  attributed mechanism. **Scope note:** decoder-prior utility *extends* plan2's literal
  "prediction-calibration only" wording (this ADR amends that wording) while staying
  inside the W1 / PLAN §1.3 boundary — both arms are deterministic re-decodings of the
  *same recorded shots*; no hardware intervention occurs and no counterfactual is
  claimed.
- **R2-full** = the composed decision-regret protocol of plan2 §3 (ranking + steelman +
  two-sided calibrated catching). It stays gated behind the taxonomy gate and the
  composed decision-regret gate, **unchanged** by this ADR.
- The **back-edge is retained and strengthened**: pre-commit (this ADR) that R2-lite
  nulls are *published* as misspecification directions, not buried — see Decision 4.

**2. The real-data ladder.** Claims at every step inherit R2-lite's restriction until
the corresponding gate fires.

- **R2-lite-a (now):** d=29 repetition-code windows on `forward/exact` (11–15q sliding
  windows; X/Z bases and sample-indexed sequential-acquisition slices as the natural
  contexts standing in for the probe ladder).
- **R2-lite-b (after the carrier feasibility study, or earlier with declared window
  caveats):** surface-code d=3 plaquette/boundary windows from the 72Q sets. The
  measured **window-closure violation is itself a deliverable** — a located map of
  correlation mass the pij/window abstraction cannot express, *consistent with* the
  externally documented nonlocal microwave crosstalk and leakage tails (a
  device-documentation prior, not a twin-attributed mechanism).
- **R2-full:** behind its gates, as in plan2 §3.
- **C (= R3): the d=5/d=7 surface-code twin on the scalable carrier**, entered only
  after the carrier's swap gate (do()-preservation on overlapping exact instances —
  base `p(s,m)`, `do(E→I)` ΔLER, band width matching the exact backend; PLAN.md §4)
  and the C-entry gates. This is the declared destination (Context 3).

**3. Schedule the carrier (amends ADR 0006 Decision 4's *post-HARDEN* clause to
*post-H2-support-structure-verdict* — carrier selection may now precede H3/H4; the
decision-rule prerequisite and the swap gate are unchanged).** The carrier
**feasibility study starts immediately after H2's support-structure verdict**
(ADR 0006's decision rule stays the prerequisite — the carrier must know whether it
carries edge slots). It is a written candidate comparison
against the fixed forward contract `c → p(s,m|c)`:

- (i) **detector-picture tensor network with local coherent/CPTP corrections** — the
  leading candidate; dMLE (arXiv:2602.19722) proved exact syndrome-likelihood at d=5,
  25 rounds on one GPU *for Pauli-parameterized models*, the existence proof that the
  scale is reachable; carrying CPTP coherence in it is the open part (W5);
- (ii) **MPO / quasi-1D density-matrix contraction** exploiting the syndrome-extraction
  schedule;
- (iii) **DEM-bulk + local coherent corrections** (ADR 0006 candidate (d));
- (iv) **windowed-exact + stitching** (the R2-lite-a method with its closure error
  measured) — the fallback, honest but bounded.

Output: **ADR 0008** selecting the carrier, with the swap gate unchanged. GPU-first
(ADR 0001) applies: the carrier is evaluated at RTX-5090-class assumptions.

**4. Pre-registered milestones with fallbacks.** The null is a deliverable, not a
failure; each fallback is declared here, *before any milestone runs* (the
user-directed M3/M4 contingency plan). **Theory-first rule (user directive,
2026-06-09):** each milestone's quantitative prediction is *derived*
(mathematics/physics) and recorded in `metric_results.md` **before** its run — the
HARDEN gate language (PLAN.md §3) and the predict-before-measure cross-check
(plan2.md §3) apply to R2-lite verbatim; runs verify derivations, never
explore-then-rationalize.

| # | Milestone | Falsification | Pre-registered fallback |
|---|---|---|---|
| M1 | Ingestion parity: reproduce the published detection-event fraction + pij matrix on d=29 data | disagreement beyond statistical error | fix the reader/forward — nothing downstream runs until M1 holds |
| M2 | Window-closure audit: fraction of two-point correlation mass crossing an 11q window boundary, threshold pre-registered before any fit | closure violated | windowing invalid as-is → the **violation map is the deliverable** (located non-locality no tool reports); route to H2 (correlated axis) and accelerate the carrier study (a TN carrier does not need windows) |
| M3 | Held-out per-shot syndrome NLL of the window-calibrated twin strictly beats the naive prior; report vs the pij prior on the same split | no NLL win | publish the negative + the **alias analysis**: hardware's few fixed contexts = wide alias; quantifies the probe richness real data lacks, and what calibration circuits a lab should run to close it — ADR 0004's probe-design (replicating-portfolio) guidance ("guidance, not gate"; plan2 §1.2: opportunity, not a committed method) |
| M4 | Emit a twin-calibrated `.dem`; frozen pymatching yields statistically significant %ΔLER vs (a) naive prior (required to continue) and (b) pij prior (headline target; dMLE 30.6% is the published rep-code bar) | no ΔLER win over pij | report honestly alongside the deliverables no competitor emits — per-edge bands, abstain flags, drift trajectories, non-Pauli residual maps; the twin's differentiation shifts to the uncertainty + drift + (sim-validated) counterfactual legs |
| M5 | Drift slice: sample-indexed per-window parameter trajectories; forecast next-slice NLL; **finite-sample band coverage with per-window estimation error propagated** (errors-in-variables / weighted regression — Gate B's requirement, pre-registered here; no nominal-coverage claim without it). A pass is "measured empirical coverage on hardware slices"; `predict` remains first-cut — **neither Gate B nor the H4 controlled-sim gate is satisfied by M5** | no resolvable drift signal or coverage miss | drop the H4-on-real-data claim; M1–M4 stand |

**5. Ledger the industry metrics.** METRICS.md gains a hardware-data section (forced
ladder: **rung 2** — frontier-standard, researched 2026-06-09 — for the
experiment/noise-model metrics; **finite-sample hardware restatements** of two
already-ledgered B-path metrics; **rung 3, flagged project-defined** for
window-closure leakage): ε_d (logical error per round), Λ (error-suppression factor),
detection-event fraction, pij-matrix agreement, decoder-prior utility %ΔLER, held-out
finite-sample syndrome NLL, finite-sample band coverage, the Tier-0 band/abstain rule
in the hardware regime, and the window-closure metric. Definitions, references, and
conventions live in the ledger, not here.

**6. The tool artifact is a first-class deliverable.** stim-native in (`.stim`/`.b8`),
standard `.dem` + diagnostic report (bands, abstain flags, drift) out; pip-installable;
one quickstart; **no new formats; no decoder**. The no-console-scripts stance is
relaxed exactly once — a single entry point — when M4 lands, not before.

## What this ADR explicitly does not do

- **No claim-boundary movement** (per Status). PLAN.md §1.3 and TWIN.md hold verbatim;
  R2-lite's one extension of R2's literal wording — decoder-prior utility — is a
  deterministic re-decoding of recorded shots (Decision 1, scope note), not an
  intervention.
- **No Claim-B engine** (per Status). Honesty at R2-lite is carried by Tier-0 bands +
  abstain-when-within-band, reported **indicative, not certified-covering** — the
  decision-regret gate showed a local/linear band under-covers at curved aliases, and
  that caveat travels with every band number (METRICS.md hardware section). Re-open
  triggers (any one suffices): an external consumer of the R2-lite report demands
  certified worst-case coverage; a certified global method (SDP relaxation /
  continuation with guarantees) appears; R2-full preparation begins. Note ADR 0004 D3
  still binds the band as methodology — this is deferral, not abandonment (abandonment
  would need its own ADR).
- **No carrier choice today** — Decision 3 schedules the study; ADR 0008 chooses.
- **No HARDEN abandonment.** H2 remains the current cut and is the *simulation twin* of
  the windows' expected residual (Google's correlated-error wedge — leakage + CZ
  stray-interaction ZZ/swap errors — ≈17% of the error budget, H2 twinning its
  stray-coupling component; documented nonlocal crosstalk is the predicted closure
  violator). H3/H4 are sequenced by R2-lite residuals via the back-edge instead of
  being built blind.

## Consequences

- `plan2.md` §3 gains a short amendment paragraph and `PLAN.md` §5 a one-line
  cross-reference to this ADR.
- METRICS.md gains the hardware-data ledger section (Decision 5).
- `configs/` and `outputs/` gain their first twin-era artifacts: R2-lite runs are
  recorded, dated outputs (per METRICS.md's no-stale-numbers rule, headline values go
  to `metric_results.md`).
- The scooping stance (Context 1) is recorded: priority is claimed on the twin
  composition, not on any single point result.
- The d=5/d=7 surface-code destination is now written down, which makes the carrier
  question schedulable instead of indefinitely deferred.

## Milestone status & derived revisions (2026-06-09 end-of-day addendum)

Execution status after day one, with table revisions derived from what the runs taught
(each revision is a pre-run correction for the next milestone, not a post-hoc edit of a
finished one):

| # | Status | Revision (and why) |
|---|---|---|
| M1 | **DONE** (`metric_results.md` M1 RESULTS; PASS, P4 adjudicated via the C1 artifact control) | As registered, M1's anchor moved from "published detection fraction" (none exists for the d=29 rep code) to bit-exact reproduction of the release's own derived data + a derived fraction band — both held. Back-edge outputs: device mirror-diagonal class (≈970× SI1000 sim), long-range tails (both families), early-layer transient. |
| M2 | **DONE** (`metric_results.md` M2 RESULTS; W2 adjudicated — the single located grid-adjacent pair (18,21) ⇒ {15,19} excluded-and-flagged, 19 clean windows licensed for M3 at margin 2) | The closure threshold was **derived from M1's measured class means** instead of guessed: interior X1 measured 17.6% vs predicted ≈18%; the registered gate moved to the margin-2 interior metric before the run. |
| M3 | **DONE 2026-06-10, regrets closed by the A1–A3 addendum** (`metric_results.md` M3 RESULTS + ADDENDUM; **P3 gate PASS both bases** — held-out ΔNLL(naive − twin) +56.2 X / +44.3 Z nats/shot/window at one-sided 99%; drift-isolated fallback corroborates; the "beats pij-DEM" claim survived its budget-rescale control STRENGTHENED — the pinned arm is already the budget-feasible family member) | Findings (A1-revised): the pij arm's deficiency is STRUCTURAL — the bunching correlation kind is unrepresentable by independent edges (the rescale control was a no-op, s_W=1; P10's global deficit stands but does not bind window constructions); per-window bunching R̂ is a split-stable located property ∈ [1.000, 17.7] (≥2 on 17/19 X / 16/19 Z; w20 = 1.000 both bases; w8 ≈ 16–18 both); P7's f̂ miss was a coordinate artifact — on the identified flip rate r̂ the original bands PASS (84.2%/80.7% in band; edge absorption +1.8e-3/+2.5e-3, sign as derived); inter-sample drift ≈44 nats/shot (M5 feed). Execution: 236 fits, all RTX 5090 static-Kraus-input CUDA graphs, P1h bit-exact throughout. |
| M4 | unchanged + two execution facts | The only shipped decoding pathway on d29 is the RL-prior MWPM → the published-checkable baseline is `XOR(obs_flips_predicted, obs_flips_actual)`; the pij-prior arm is self-computed (M1 pipeline already produces it). **New dependency decision to register with M4: pymatching** (the in-repo MWPM is small-code only). dMLE 30.6% bar unchanged. |
| M5 | re-worded (already in Decision 4) | "Run-stamped" was wrong — the d29 release has **no timestamps** (100 sequentially indexed samples/basis); M5 slices by sample index. Gate-B constraint (errors-in-variables propagation before any nominal-coverage claim) stands. The richer drift data for later: `set1` (16 sequential experiments / 15 h) and `set2` (deliberately mixed calibration freshness) — surface code, windows only. |
| — | **new parallel item** | **ADR 0008 carrier feasibility study**, unblocked by H2's support-structure verdict (Decision 3): runs in parallel with M2 — the new pair replacing the original "H2 ∥ M1/M2". |

## References

- Local datasets: `/home/cx/Document/google_72Q_repetition_code_d29`,
  `google_72Q_surface_code_d3_d5_set1/2`, `google_105Q_surface_code_d3_d5_d7`
  (Zenodo 13273331 family; Google Willow, arXiv:2408.13687, Nature s41586-024-08449-y;
  Google 2023, Nature s41586-022-05434-1).
- Field bars and methods: Spitz et al. arXiv:1712.02360 (pij); Sivak et al. PRL 133,
  150603 (RL-optimized DEM priors); Cao et al. arXiv:2602.19722 (dMLE — closest prior
  art and the d=5 TN existence proof); Hockings et al. arXiv:2502.21044 (ACES
  noise-aware decoding, exponential-in-d gains); Takou & Brown arXiv:2504.20212,
  2510.23797 (hyperedge/coherent DEM estimation); AlphaQubit, Nature
  s41586-024-08148-8; stim (Gidney, Quantum 5:497) and pymatching v2.
- Project spine: ADR 0002 (build order; its C option names the stim-ingestion
  bridge), 0003 (B methodology), 0004
  (bands, D1–D5), 0005 (SCOPE retired), 0006 (channel field; carrier deferred —
  timing amended here); `tests/test_decision_regret_gate.py` + `metric_results.md`
  (2026-06-09 verdict); PLAN.md §3 (HARDEN status), plan2.md §3 (rungs, back-edge).
