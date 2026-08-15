# E1 exact-small falsifier + dual-oracle qualification — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-04. Predictions written BEFORE any oracle or candidate
computation; a miss is a finding, not a re-fit. Closure packet:
`outputs/temporal_memory_survey_2026-08-04/` (00–08; adversarial verification `04E`). Frozen
instance/corruption/oracle specification: `outputs/temporal_memory_survey_2026-08-04/07_FALSIFIER_AND_NEXT_EXPERIMENT.md`
(v2, §§1–10) — this preregistration binds that spec by reference and restates only load-bearing
identities. This document authorizes no code; implementation start remains a separate owner
decision (`theory-first` orchestrator + repo `src/**` rule; E1 plans no `src/**` changes).

## -1. Question charter (importance × attackability)

- **Decision + consequence.** Qualify (or refute) the four Direction-1 exact-core primitives —
  P1 hybrid forward filter, P2 affine-collapse HMM filter, P3 tilted-transfer Fourier engine +
  WHT inversion, P4 WFA realization + equivalence verdicts — on frozen memoryful instances, with
  a dual independent oracle substrate. If qualified: these become the reference/oracle layer that
  E2 (production-sampler substrate qualification), E3 (G-A certificate theorem test bed), and E4
  (analytic-cell derivation checks) all consume, and the first executable evidence that the ECS
  capability set (SAMPLE/SCORE/PREFIX/FUNCTIONAL/STRUCTURED/ENUMERATE) is servable for declared
  finite-memory processes. If refuted: the failure localizes to an implementation or to a frozen
  semantic ambiguity (see kill condition) before any scaling work is attempted.
- **Plausible attack + independent anchor.** All instances are finite and exactly enumerable
  (≤ 4096 rational trajectory terms for F1–F3; < 10^6 for F4; windowed F5); the exactness of
  every primitive's target identity is either elementary (finite total probability) or anchored
  to verified sources (ledger §0). Nothing here needs asymptotics, truncation, or sampling to be
  decided.
- **Alternative formulations + invariants.** The same law must emerge from (i) trajectory
  enumeration (O1), (ii) dense instrument-chain evolution (O2), (iii) each primitive under test;
  invariants that must agree across all: exact normalization, support algebra (§2a-A rows),
  private-state gauge invariance (C7), shot-contract semantics (RESET product law).
- **Kill condition.** O1/O2 disagreement beyond the float gate that survives independent bug
  audit — i.e., a genuine semantic ambiguity in the frozen object definition
  (`00_PROBLEM_DEFINITION.md`) — stops E1 and reopens the definition freeze. Any inert
  corruption row (C1–C9 producing no precomputed-difference trip) invalidates the battery and
  stops qualification claims until repaired.
- **Selection warning.** E1 is chosen for dependency dominance (E2–E4 consume its outputs), not
  difficulty or fashion; it carries zero scientific-novelty claims of its own.

## 0. Grounding ledger

| sub-axis / mechanism | anchor artifact | verification grade | in-repo code (reuse) |
|---|---|---|---|
| Instrument-chain outcome law composition (finite memory, exact) | arXiv:0904.4483v2, Def. 2/Eq. (14) link product; Eq. (19) Born rule via composition; Thm 3/Eq. (25); Eq. (35)+Eq. (66) for probabilistic networks | `04E` V1 (CORRECTED, quotes + locators; note: evaluation-cost statements are NOT the paper's) | — |
| Finite-memory outcome-sequence laws = transfer-operator products (exact scoring) | arXiv:1803.08220 (PRL 121, 260602), Thm 1/Eq. (10); Eq. (12); Supp. A (Eq. S4) + Supp. D (Eqs. S17–S18) — NOT "Supp. S3" (ar5iv artifact) | `04E` V2 (CORRECTED) | — |
| Prefix-conditional exact sampling from scoring (incl. adaptive circuits) | quant-ph/0511069v4 Sec. 6, Lemmas 6.1–6.2 + 3-step procedure | `04E` V5 (CONFIRMED); repo reading note `docs/papers/reading_notes/markov_shi_tensor_contraction_quant_ph_0511069v4_source_review.md` | — |
| Sampling from prefix-probability oracles with mid-circuit measurement + classical control | arXiv:2112.08499 (PRL 128, 220503), Algorithm 2 + inline correctness claim ("each gate may be classically controlled by outcomes of all previous measurements"; oracle = prefix-subcircuit probabilities) | `04E` V6 (CONFIRMED; not a numbered theorem — do not cite as one) | — |
| Metric ladder | `docs/METRICS.md` Record-certification rows (TV, SYNDROME_DIST, DETECTOR_MARG, RR_CORR, SCALAR_FUNC) | in-repo ledger, owners + unit tests named there | `certify/core.py`, `certify/types.py` |
| Registered corpus-note debt | 0904.4483 and 1803.08220 have `04E` verification records (verbatim quotes + locators) but no corpus reading notes; debt activates only if these anchors are promoted beyond E1 design rationale | — | — |

E1's correctness chain deliberately routes through the dual oracles and hand-derived class-(a)
identities below, not through the papers: the anchors are design provenance. No open,
contradicted, or abstract-grade row is used as a premise.

## 1. Mechanisms (declared fixtures; no physical-truth claim)

Instances F1–F5 exactly as frozen in `07` §§1–8 (3-qubit bit-flip repetition code, T=3, two
Z-checks per round, final transversal readout; D=8 detectors (2 per round + 2 final-closure),
O=1 observable = final qubit-1 readout parity against the declared all-zero reference; all
parameters rational; F1 telegraph memory π=(1,0), K=[[9/10,1/10],[2/10,8/10]], p(0)=1/100,
p(1)=1/5; F2 support restriction to qubit-2-only errors; F3 rates p(0)=10⁻⁴, p(1)=10⁻³,
K=[[1−10⁻⁶,10⁻⁶],[1/2,1/2]]; F4 adds memory-modulated measurement flips q(m) (q(0)=1/50,
q(1)=1/10) + one declared feedback; F5 S=3 shots, HOLD and ADVANCE_DECLARED variants, declared
3-detector window per shot). These are controlled fixtures; fixture values never become measured
parameters. Swept ranges: none — every parameter is frozen (this is a qualification experiment,
not a mechanism sweep).

## 2. Metric binding (forced standard-metric ladder)

- **Existing `docs/METRICS.md` entries used, unmodified:** full joint Record distance
  `TV(p,q)=0.5·Σ|p−q|` (owner `certify.core.total_variation`); detector-record marginal distance
  (`Statistic.SYNDROME_DIST`); detector/observable marginals (`Statistic.DETECTOR_MARG`);
  round-to-round detector correlation (`Statistic.RR_CORR`, Pearson on binary columns, reduce
  `mean_j abs`); registered scalar identity (`Statistic.SCALAR_FUNC`).
- **Registered comparison-band debt (project-defined, justified):** for F3's strictly positive
  sub-1e-12 record probability, the ledgered scalar absolute band (1e-9) is registered here as
  an **insufficient statistic** — an absolute band passes a silently-zeroed value. E1 binds F3
  to (i) exact rational equality in the ALGEBRAIC_EXACT tier (class (a), zero tolerance) and
  (ii) relative error `|v−v_ref|/v_ref ≤ 1e-6` in the floating tier. Same quantity, stricter
  band; follow-up: propose a relative-band scalar row for the METRICS ledger.
- **Forbidden proxies:** per-round detector marginals may NOT stand in for the joint law (F1 is
  marginal-matched by construction — the discriminator lives in cross-round structure);
  `NUMERICAL_ZERO=1e-12` may not adjudicate structural zeros (support rows are class (a)
  algebra); sampler empirical agreement may not certify scorer correctness.
- **Derived statistics (registered here, TV-formula reuse):** exchangeability defect
  `TV(law, shot-permuted law)` for F5; corruption deltas `TV(corrupted, true)` for C1–C9.

## 2a. Predicted observables (registered before any computation)

Class (a) exact rows (theorem/derivation; zero tolerance):

- **A1 (F1/F3 closure zeros).** With perfect measurements and no post-round-3 error window, both
  final-closure detectors are structurally zero (final-readout syndrome ≡ last measured
  syndrome). Every law entry with a closure bit set is exactly 0.
- **A2 (F2 support law).** With qubit-2-only errors and perfect measurements,
  `d[r,c1]=d[r,c2]` for every round r; the support is exactly the affine set this implies;
  everything off it is structurally zero (algebraic, parameter-independent within the family).
- **A3 (F1 rival independence).** For the marginal-matched IID rival with perfect measurements,
  detectors in distinct rounds are functions of disjoint independent variables: RR_CORR = 0
  exactly.
- **A4 (RESET product law).** F5 under RESET equals the S-fold product of the single-shot law
  exactly.
- **A5 (gauge invariance).** Relabeling private memory states with matched kernel/rates (C7
  pair) leaves the public law bit-identical.
- **A6 (normalization).** Every law sums to exactly 1 in rational arithmetic.
- **A7 (F3 positivity).** μ(r*) > 0, witnessed by an explicitly exhibited generating trajectory
  (memory path × flip pattern) written down before O1 runs.

Class (b) prediction bands (falsifiable bets; a miss is a finding):

- **B1 (F1 discrimination).** `TV(law_mem, law_iid) ∈ [1e-4, 1e-1]`, and the discriminating
  structure is cross-round: `SYNDROME_DIST` restricted to any single round ≤ 1e-12 (marginals
  match by construction) while the joint TV falls in the band.
- **B2 (F1 persistence sign).** Persistent-process RR_CORR strictly positive, band
  `mean_j |corr| ∈ [1e-3, 0.3]` for adjacent rounds (positively persistent kernel ⇒ positive
  firing-rate covariance).
- **B3 (F3 magnitude).** `μ(r*) ∈ [1e-17, 1e-15]` (dominant path ~(10⁻⁴)⁴ with O(1)
  combinatorial multiplicity).
- **B4 (F5 order sensitivity).** HOLD exchangeability defect `TV(law, permuted) ∈ [1e-4, 1e-1]`;
  ADVANCE differs from HOLD by TV > 1e-6; both collapse to 0 under RESET (ties to A4).
- **B5 (F4 non-degeneracy).** Measurement noise activates the closure detectors
  (P[closure bit = 1] ∈ [1e-3, 0.2]) and the declared feedback changes the law vs the
  feedback-off control by TV > 1e-4.

Class (c) gates: O1/O2 float agreement ≤ 1e-13 per entry; e-process sampler checks at α=1e-3
(Ville-valid, optional-stopping-safe); resource caps 300 s / 8 GB per call with
`CENSORED_RESOURCE` semantics.

## 2b. Disconfirmation surface

- **Strongest competing explanation for a clean pass:** shared-bug agreement (O1, O2, and a
  candidate agreeing because they encode the same misreading of the frozen semantics).
  Separators registered in advance: structural independence of the oracles (combinatorial
  rational enumeration vs dense complex128 linear algebra; disjoint authorship, no shared
  helpers); the hand-derived class-(a) rows A1–A7, which are proved on paper and would each
  catch a coherent shared misreading of layout, support, gauge, or shot semantics; and the
  corruption battery, whose deltas are precomputed from the declared semantics and trip only if
  the implementations actually consume the declared inputs.
- **Prospective null searches:** A3 (an exact zero where naive intuition expects correlation)
  and A4 (exact product law) are run as nulls, not only positives.
- **What would distinguish failure modes:** O1≠O2 → implementation or semantic ambiguity (kill
  path); O1=O2≠candidate → candidate refuted on that cell; corruption inert → battery invalid
  (no candidate claims); band miss with class-(a) rows intact → registered finding about the
  fixture, never silently re-banded.

## 3. Independent ground truth (non-circular)

- **O1**: exact rational trajectory enumeration (`fractions.Fraction`, no floats anywhere) —
  from-scratch, no simulator imports.
- **O2**: dense instrument-chain evolution on H_S ⊗ H_M (complex128), memory as a diagonal
  register, sequential conditioning — structurally different mathematics, disjoint authorship
  (separate builder, no shared code with O1).
- **O3 (optional corroborator)**: independently authored Storm-`--exact`/WMC+XOR lowering of
  F1/F2.
- **Hand derivations**: A1–A7 rows are paper-proofs checked against both oracles; the F3 witness
  trajectory is written before O1 exists.
- The primitives under test (P1–P4) are never their own reference; P4's equivalence verdicts are
  judged against exact PMF equality/inequality from O1 (Tzeng's theorem is design rationale,
  not the ground truth).

## 3a. Constraint ledger + corruption falsifiers

| constraint | exact assertion | falsifying test | deliberately broken input | evidence test trips |
|---|---|---|---|---|
| Layout is consumed, not assumed | law changes exactly as precomputed under operand swap / constant flip | C1, C2 | swapped `columns` between two rows; flipped constant | precomputed nonzero TV + changed-entry list must be reproduced |
| Layout identity binds | binding identity changes even when law is invariant | C3 | row-order permutation without consumer relabel | identity-hash mismatch caught; law unchanged (paired control) |
| No undeclared memory reset | joint law ≠ reset law | C4 | kernel reset inserted at round-2 boundary | precomputed TV > 0 reproduced; per-round marginals near-preserved (catches marginal-only validators) |
| Shot order is semantic under HOLD | permuted-order law ≠ law | C5 | shot-permuted acquisition | exchangeability defect reproduced (B4) |
| Contract honesty | stateful acquisition may not be relabelled independent | C6 | HOLD batch declared INDEPENDENT_REPLICATE | support-decision-level rejection required, not a numeric fudge |
| Evaluator-truth isolation + gauge | leak visible; relabel invisible | C7 | memory bit copied into a record column; memory labels permuted with matched kernels | leak: law differs from truth; gauge: bit-identical law (A5) |
| No silent truncation | sub-1e-12 mass survives | C8 | oracle variant dropping trajectories with mass < 1e-10 | F3 record becomes 0 → flagged as guarantee violation (with the §2 relative-band rule, not the absolute band) |
| No silent process substitution | IID answers to memory queries detected | C9 | E_iid silently served for F1 | discriminating cross-round statistic trips (B1/B2) |
| Structural zeros exact | A1/A2 rows exactly zero in every output | support tests | pseudocount/floor variant | any nonzero mass on off-support rows fails |
| Normalization exact | Σp = 1 rational | A6 test | one branch weight perturbed by 1e-15 | rational sum ≠ 1 detected exactly |

Every row's trip evidence must be produced (the corruption actually fired) before the clean-pass
row may be closed — a clean-only pass closes nothing (Faithfulness Rule II).

## 3b. Negative controls + non-degeneracy

- **Inert control expected to FAIL:** source-off (p(0)=p(1)=0) must yield the deterministic
  all-zero record point mass; any other mass = fail. C3 is the paired inert-by-design control:
  the *law* must NOT change (only the identity hash) — if the law changes, the harness itself is
  broken.
- **Object movement:** memory knob p(1): 1/5 → 1/100 must drive `TV(law_mem, law_iid)` below
  1e-6 (degenerate limit), and restoring p(1)=1/5 must restore B1's band — the knob moves the
  measured object.
- **Strongest competing explanation** and its separator: §2b (shared-bug agreement vs
  independent-structure + hand-proof rows).

## 4. Bounded simplifications

- Perfect measurements in F1–F3: an instance property of declared fixtures, not an approximation
  of a target — no bound owed; F4 covers the noisy-measurement mechanics.
- Floating tier (O2, float candidate modes): bounded by the 1e-13 agreement gate against O1's
  rationals and the F3 relative band; the rational tier owes nothing.
- Windowed F5 record (3 declared detector bits per shot): part of the declared layout identity,
  not a truncation of a wider object.
- No truncation, cutoff, discretization, or reduction exists anywhere in E1 — there is no
  unbounded simplification to stop on.

## 5. Epistemic status

- (a) exact: A1–A7; corruption-delta reproduction in rational mode; O1's laws once computed
  (enumerated values); support algebra.
- (b) bands: B1–B5. A miss is a reportable finding about the fixture design; bands are never
  re-fit post hoc.
- (c) gates: float agreement 1e-13; e-process α; resource caps; verdict vocabulary
  (COMPLETED / CENSORED_RESOURCE / FAILED).
- Headline verdict stays PROVISIONAL and per-primitive: "P_k qualified on F1–F5 cells at the
  declared guarantee tier" — no family qualification beyond the frozen cells, no scaling claim,
  no FULL_RECORD_LAW_CERTIFIED claim beyond the enumerated instances, nothing built on a (b)
  band.

## 6. Build org

- Builder A: O1 + corruption-delta precomputation (rational only). Builder B: O2 (dense,
  complex128), no access to A's code. Builder C: candidate primitives P1–P4 against the frozen
  interfaces. Disjoint files; orchestrator-driven runs; committed scripts with printed evidence
  and `__main__` guards; no `src/**` changes.
- Reviewer: un-led — receives the frozen spec (`07`), this preregistration, and the produced
  artifacts only; no expected-answer briefing.
- Execution order (two-stage, registered): (1) oracle freeze — O1/O2 built, A1–A7 checked,
  corruption deltas computed and hashed; (2) candidate runs — P1–P4 scored against the frozen
  oracle artifacts. Stage 2 may not begin until stage 1's artifacts are hashed and published.

---

Gate: `premises closed? yes | standard metric bound? yes (registered band-debt for F3 declared) |
predictions frozen? yes (A1–A7, B1–B5, before any computation) | independent GT? yes (O1/O2
disjoint authorship + hand derivations; optional O3) | constraint falsifiers registered? yes
(C1–C9 + support/normalization rows, each with a required trip) | simplifications bounded? yes
(none unbounded; no truncation exists) | controls registered? yes (source-off, C3 inert-by-design
pair, knob movement) | preregistration gate: pass`
