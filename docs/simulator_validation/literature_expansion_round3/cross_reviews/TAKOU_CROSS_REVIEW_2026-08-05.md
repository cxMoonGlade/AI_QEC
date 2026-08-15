# Independent cross-review — Takou et al., arXiv:2606.11496v2

## Decision

**REVISE.** The audit and draft source note reconstruct the paper's model, computation, hardware
scope and logical-result boundaries accurately. The row dispositions are also correct: the source
adds strong adjacent evidence for hardware-record-derived decoder priors, but it does not close
memory-conditioned benefit, wrong-memory-model robustness or frozen transfer.

Two audit phrases should be revised before admission:

1. the D2 wording currently extends “common shot ensembles and propagated shot-level uncertainty”
   across the Willow and IBM comparisons. The same-shot, covariance-aware construction is explicit
   for Willow; the IBM shot count and error-bar construction are not reported beyond the Fig. 4
   label “standard deviation”;
2. the A5 wording implies that a continuing state is central to the Remm approach. Remm directly
   represents long-lag covariance/signature structure, but it does not define a continuing carrier-
   state transition model. Takou does not reproduce Remm's long-lag signature treatment; neither
   source should be promoted to an explicit carrier-state model.

The draft source note already preserves both distinctions and requires no semantic revision from
this cross-review. No audit, source-note or manifest file was modified.

## Fixed-object verification

- Independently retrieved official source: `https://arxiv.org/pdf/2606.11496v2`.
- Official record: arXiv:2606.11496v2, *Logical error estimation from syndrome data of surface-code
  experiments*, Evangelia Takou and coauthors; v2 dated 12 June 2026. The title page gives a
  manuscript date of 15 June 2026.
- Official and local PDFs match: 19 pages, 6,078,283 bytes, SHA-256
  `4441789ebbe43aab4cae64bfda047ccd55c66c42acd9aada63fe87294767aaeb`.
- The duplicate retained source at
  `outputs/overview/literature/final_expansion/sources/2606.11496.pdf` has the same hash.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/TAKOU_SYNDROME_DEM_2606_11496_AUDIT_2026-08-05.md`,
  SHA-256 `2c10da274523305db667ad3911b7be80cf0fed91e1cb2eca3cf0fb7bd328b960`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/takou_syndrome_dem_2606.11496v2_source_review.md`,
  SHA-256 `24cc155c64b4ca8dc620b65ac929bf336befdeefbcd3d920f82479c3c1702c14`.
- The draft contains 14 `paper_fact` and three `literature_gap` records. Its source and audit hashes
  match the fixed files. Full `parse_note(..., verify_artifact=True)` admission is intentionally
  blocked by its current `evidence_status = "unpersisted"` and
  `admission_status = "draft_not_admitted"`; this is the expected pre-admission state, not a schema
  defect found by the cross-review.
- Independent reading covered all 19 pages. The Willow protocol and results, IBM protocol and
  results, moment inversion, temporal-rate diagnostics, correlated-MWPM comparison, logical-rate
  fits and uncertainty discussion were visually checked on rendered PDF pages 2--5, 9--10, 12--14
  and 16--17.

## Independent scientific reconstruction

### Representation, interface and computation

The estimated object is an independent-event detector error model on detector/logical-observable
support inherited from a reference model. Willow uses either SI1000 or RL-optimized support and its
associated hyperedge decomposition; IBM uses undecomposed support from an IBM-like circuit model
and then the same graphlike decomposition as that reference. The procedure changes event
probabilities. It does not discover an unrestricted new support, new logical-observable assignment
or new decomposition.

For each declared support set, the estimator uses empirical detector moments for its nonempty
subsets and performs hierarchical strict-superset inversion. The implemented event support is
restricted to detector sets of size at most four, so the required moments extend through fourth
order. This is a maximum interaction/moment order, not a temporal-memory order. The method assumes
independent Bernoulli events on the supplied support.

Unresolved negative correlator signs are assessed with a 100-bootstrap sign check. Selected
unresolved values receive a positive floor, and selected invalid probability solutions are zeroed;
rates above one half are capped only where required by the correlated-MWPM implementation. These
operations matter to estimator validity and decoder compatibility, but they are not evidence for a
physical memory law.

The QEC-facing interface is a DEM prior supplied to MWPM. The main comparison therefore tests
whether record-estimated probabilities on a chosen support improve logical decisions relative to
reference probabilities. It does not test whether the decoder benefits from access to a continuing
physical or latent state.

### Willow and IBM scope

The Willow analysis uses released rotated-surface-code X- and Z-memory records, 50,000 shots per
experimental instance, distances 3, 5 and 7, multiple distance-three subsystems, and available cycle
counts drawn from 1, 10, 13, 30, 50 and 70. The reference SI1000 and RL models can differ in both
probability values and hyperedge decomposition; the corresponding estimated model retains the
chosen reference's support/decomposition.

The manuscript explicitly states that each Willow prior is estimated from the same 50,000 shots
that are subsequently decoded. Logical success/failure labels are not used during prior estimation,
but there is no held-out prior-estimation/evaluation split. Willow delta-method error bars propagate
the binomial variances and covariance of the two logical estimates obtained on the common shot
ensemble. They do not propagate resubstitution uncertainty from estimating the prior on those same
shots, and Appendix H excludes common-mode device fluctuations and some SPAM-calibration contrast
uncertainties.

The IBM analysis uses new unrotated distance-three X- and Z-memory records from `ibm_miami`, through
19 syndrome-extraction cycles, without dynamical decoupling and with XY4. Ancillas are not
unconditionally reset, so detectors compare corresponding outcomes two cycles apart. The paper
does not state the IBM shot count. It says that the estimation follows a similar procedure, but Fig.
4 identifies uncertainty only as “standard deviation”; it does not document the common-shot or
delta-method construction at the specificity given for Willow.

### Logical benefit and uncertainty

The primary logical observable is finite-memory logical error probability after a declared number
of cycles, including its fractional change under alternative priors. Across the displayed Willow
instances, syndrome-estimated priors usually improve on SI1000, reaching about ten percent in
selected cases; ordering relative to the RL prior varies by instance. Across the displayed IBM
conditions, improvements relative to the IBM-like prior are commonly about five to ten percent,
with larger reported single-cycle Z-memory point estimates of about 37 percent without XY4 and 18
percent with XY4. The IBM-like reference is not calibrated to the effective idle-noise suppression
introduced by dynamical decoupling, which weakens that comparison as an isolated test of syndrome
estimation.

Appendix E crosses IBM-like versus estimated priors with standard versus correlated MWPM and shows
that prior estimation and the correlated decoder can give complementary reductions. It is a useful
prior-by-decoder comparison, but the correlated-MWPM input includes the stated probability capping
and the result still does not vary temporal-state access.

Appendix H also converts Willow finite-cycle probabilities to fitted per-cycle logical error rates
and suppression factors. Those fits assume a time-independent logical failure probability per cycle
and no offset. The estimated-prior point estimates are consistently lower in the tabulated per-cycle
rates, but uncertainties overlap, and the fitted suppression factors agree within error bars. The
source does not report a pooled effect or a hypothesis test that would turn the displayed instances
into a field-wide benefit estimate.

### Temporal-memory and attribution status

The analysis keeps cycle-translated detector locations distinct, so inferred event probabilities
can vary with cycle position. It also reports detector covariances, periodic families and rate
growth. These observations establish temporal inhomogeneity or record correlation. They do not
define a carrier lifetime, latent-state transition, history-conditioned event law or formal quantum
non-Markovianity.

For IBM, leakage accumulation and coherent ZZ crosstalk are discussed as plausible explanations for
selected trends and dynamical-decoupling-sensitive features. The DEM inversion does not identify
either cause uniquely. Willow's flatter rates and isolated reproducible spikes likewise do not by
themselves identify reset efficacy or a microscopic carrier. The paper appropriately treats
detector statistics as insufficient for unique physical attribution.

No comparison changes a history window, randomizes record order, suppresses a declared carrier,
holds a temporal model fixed under a wrong lifetime, or deploys one frozen estimated prior across
devices, distances or operating regimes. Cycle-dependent DEM probabilities therefore cannot be
used as a proxy for memory-conditioned benefit, wrong-memory-law robustness or frozen transfer.

## Assigned-row cross-check

| row | independent finding | audit/note treatment | result |
|---|---|---|---|
| D1 — hardware memory-conditioned decoder benefit | Hardware syndrome records are converted to effective priors and evaluated logically, but no arm removes access to a continuing state, changes a history window or randomizes order. | The missing/adjacent disposition is correct. | **pass** |
| D2 — population-level matched decoder comparison | Willow has broad same-task comparisons using the same MWPM family and common 50,000-shot ensembles, with covariance-aware logical uncertainty, but prior fitting and evaluation reuse those records. IBM adds multiple hardware conditions, but its shot count and uncertainty construction are unspecified. Neither is a memory-access ablation or a declared population sample. | The disposition is correct; scope the common-shot/covariance statement explicitly to Willow. | **revise wording** |
| R1 — wrong-memory-model robustness | Sign bootstraps, support omissions, probability regularization and reference-prior comparisons probe estimator/static-prior limitations. No frozen decoder is exposed to a wrong temporal law, lifetime, mixed carrier or stale calibration. | Correctly missing. | **pass** |
| T1 — frozen transfer | The recipe is applied on Willow and IBM, but every instance receives newly estimated probabilities and device-appropriate reference support/decomposition. | Correctly distinguishes portability/adaptation from frozen transfer. | **pass** |
| A5 — concrete approach coverage | Takou is a concrete hardware-record-to-fixed-support-DEM-to-logical-evaluation bundle. It is not an explicit multicycle state model. | Adjacent/not-a-replacement is correct, but the contrast with Remm should refer to long-lag signatures rather than a continuing state. | **revise wording** |

## A5 representativeness: Takou versus Remm

The two sources serve different overview functions.

Remm directly analyses same-auxiliary covariance over lags through `Delta m = 11`, fits an
approximately `0.89^Delta m` tail, and selects multicycle correlation signatures spanning as many as
nine consecutive cycles. Its inversion is written for arbitrary signature order, and its retained
analysis contains 4,360 selected signatures. This makes Remm the more direct representative for an
approach whose QEC-facing object is explicit long-lag record/signature structure. It still does not
uniquely attribute that structure to leakage or define a continuing carrier-state transition model.

Takou cites and adapts the moment-inversion logic, but its decoder estimator is restricted to
supplied detector support of size at most four and is directed toward record-derived DEM priors and
logical evaluation on two hardware platforms. That makes it stronger adjacent evidence for Section
5 questions about observation, decoder-prior benefit and evidence boundaries. It does not replace
Remm as the Section 3 representative of long-lag signature inference.

The defensible synthesis is therefore to split their roles:

- **Remm:** representative long-lag covariance/signature approach; observation of multicycle
  record structure, without unique microscopic attribution or an explicit carrier-state law.
- **Takou:** representative fixed-support effective-model/prior approach; hardware-record logical
  comparison, without a memory-access treatment, held-out prior evaluation, wrong-memory stress
  test or frozen transfer.

## Required audit revisions

1. In D2, replace the broad common-shot/uncertainty clause with wording such as:
   “Willow explicitly evaluates alternative priors with the same MWPM family on the same
   50,000-shot ensembles and uses covariance-aware delta-method error bars. IBM reports analogous
   prior/decoder comparisons, but its shot count and error-bar construction are not stated beyond
   ‘standard deviation’.”
2. In A5, replace the current “source does not say” sentence with wording such as:
   “Its estimated object is an independent-event DEM on supplied support with moments through
   fourth order. It does not reproduce Remm's selected long-lag covariance/signature analysis.
   Neither paper defines a continuing carrier-state transition model.”
3. Preserve the existing D1, R1 and T1 dispositions and the source note's distinctions between
   cycle-resolved temporal structure, microscopic attribution and memory-conditioned benefit.

## Disposition

- `read_status`: complete
- official-object verification: pass
- cross-review result: **revise**
- audit scientific row dispositions: pass
- audit semantic fidelity: revise two boundary phrases
- draft source-note semantic fidelity: pass
- provenance/hash integrity: pass
- manifest action: none taken; admission remains with the parent reviewer after audit revision and
  corresponding hash/schema update

After revision, the strongest defensible use is: Takou demonstrates that syndrome-derived event
probabilities on a reference DEM support can improve finite-cycle logical decoding on Willow and IBM
records under the reported conditions. It does not demonstrate temporal-memory-conditioned decoder
benefit, unique microscopic attribution, robustness to a wrong memory model, held-out prior
generalization or frozen cross-device/cross-code transfer.

## Final verification after the requested revisions

**Final decision: REVISE for admission schema; PASS for the two scientific boundary revisions.**

The revised audit now closes both substantive issues identified above:

- D2 confines the explicit common-50,000-shot and covariance-aware uncertainty statement to Willow
  and separately states that the IBM shot count and error-bar construction are not reported at the
  same specificity.
- A5 now contrasts Takou's supplied-support DEM with Remm's long-lag covariance/signature treatment
  and states explicitly that neither source defines a continuing carrier-state transition law.

The revised audit has SHA-256
`890e1e6fdbf4a75da109499464e62fb93a35daa7b904a0db88563802dd1cd95e`, and the draft source note
contains that exact value in `audit_packet_sha256`. The fixed local and retained-copy PDFs remain
byte-identical at SHA-256
`4441789ebbe43aab4cae64bfda047ccd55c66c42acd9aada63fe87294767aaeb`. The revised draft note has
SHA-256 `fd27d4da433c22ddaf70846923cb07b28dd99a5b03c4bd510d66eeb19de7de7d`.

Prospective admission-schema validation found two remaining source-note metadata/locator blockers:

1. `Selection scope` uses `Source locator: Abstract and Introduction`, which lacks the exact
   page/section/figure/equation anchor required by `_valid_locator`. It should name an exact anchor,
   for example `Abstract, p. 1; Introduction, pp. 1--2`.
2. `Moment-inversion computation` is anchored to PDF page 9, but page 9 is absent from
   `visually_checked_pages = [1, 2, 3, 4, 5, 6, 13]`. Page 9 was independently rendered and checked
   in this cross-review; admission metadata must record that check before the fact can pass schema.

With only the admission-status, locator and visual-page gates bypassed diagnostically, the remainder
of the note validates: 17 evidence records (14 `paper_fact`, three `literature_gap`) and five
relations, with artifact and audit hash verification enabled. The raw note correctly remains
non-admissible while it declares `evidence_status = "unpersisted"` and
`admission_status = "draft_not_admitted"`.

Accordingly:

- scientific interpretation and row dispositions: **pass**;
- revised audit semantics and hash linkage: **pass**;
- source artifact identity and hash: **pass**;
- source-note admission schema: **revise** on one locator and one visual-page declaration;
- manifest action: none taken.

No source note, audit or manifest file was changed during this final verification.

## Final schema re-verification

**Final decision: PASS for pre-admission review.** Both remaining schema blockers are closed while
the scientific wording approved above remains unchanged.

- `Selection scope` now uses the accepted exact locator
  `Abstract, p. 1; Introduction, pp. 1--2`.
- PDF page 9 is now included in `visually_checked_pages`, matching the page anchor for the
  moment-inversion fact.
- The fixed official and retained-copy PDFs remain byte-identical at SHA-256
  `4441789ebbe43aab4cae64bfda047ccd55c66c42acd9aada63fe87294767aaeb`.
- The audit remains SHA-256
  `890e1e6fdbf4a75da109499464e62fb93a35daa7b904a0db88563802dd1cd95e`, and the note declares that
  exact audit hash.
- The schema-corrected draft note is SHA-256
  `4b6f09c8efc975249beee31406a70eed4525850128a29b18ff8dbdeddfc1a226`.

A read-only prospective artifact-verifying parse, changing only the intentional draft admission
values in memory, succeeds with 17 evidence records (14 `paper_fact`, three `literature_gap`), five
relations and eight declared visual-check pages. The standard directory audit continues to exclude
the note solely because it is deliberately marked `unpersisted` and `draft_not_admitted`; this is
the expected pre-admission state.

Final disposition:

- scientific interpretation and row dispositions: **pass**;
- audit semantics and hash linkage: **pass**;
- source artifact identity and hash: **pass**;
- pre-admission schema readiness: **pass**;
- manifest action: none taken.

No source note, audit or manifest file was changed during this re-verification.
