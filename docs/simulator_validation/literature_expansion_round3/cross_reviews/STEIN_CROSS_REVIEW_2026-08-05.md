# Independent cross-review — Stein et al., arXiv:2601.16123v1

## Decision

**REVISE.** The audit correctly identifies the paper's most important transfer boundary: the
learned GCN/FiLM/CNN parameters are applied to new Kingston chains and a later calibration
snapshot without retraining or fine-tuning, but fresh target calibration is still processed and, in
folded mode, changes the effective convolution weights. This is within-seen-device,
target-calibration-conditioned transfer, not calibration-blind, unseen-device, cross-configuration or
cross-code transfer. The memory-law, uncertainty and latency non-promotions are also substantially
correct.

Two scientific claims in the draft note are nevertheless false as written. `stein-validation-result`
and `stein-unseen-transfer-result` say FiLM has lower LER than both comparators across all tabulated
settings. Tables III--VI contain many contrary shallow and intermediate configurations. In the 40
one-week-later rows, FiLM is strictly lower than both comparators in 14 rows; several other rows favor
only one comparator, tie, or favor neither. The source itself describes a configuration-dependent
crossover, not universal superiority.

The audit's `D2` label is also too strong. This is a broad, matched, multi-configuration hardware
comparison, but the later Kingston target population is not enumerated, the chain/snapshot selection
rule and exclusions are not given, per-configuration shot counts are absent, and the interval and
pairing procedures cannot be reconstructed. It should not be called a closed population-level
comparison without defining “population” as merely the printed `(basis,d,r)` design grid.

Finally, the audit records the PDF as version 1.5 although the official/local byte stream begins
`%PDF-1.7`, and all five draft relations fail the current schema. These require revision before
admission.

## Fixed-object verification

- Official record: arXiv:2601.16123v1, submitted 22 January 2026, Samuel Stein and eight coauthors.
  The official version history listed only v1 at review time.
- Official PDF streamed from `https://arxiv.org/pdf/2601.16123v1` and the fixed local artifact are
  byte-identical: 18 pages, 696,762 bytes, SHA-256
  `f09848cdf8ed099ebf213750bdbf397a92659f04c4e8c6e5177454821b3de50e`.
- The PDF is version **1.7**, not 1.5: both the file header and `pdfinfo` report 1.7.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/STEIN_FILM_DECODER_2601_16123_AUDIT_2026-08-05.md`,
  SHA-256 `24651159b51b465e177eab20f314580033e006160f8caf66b07e9a9c7ddae422`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/stein_film_decoder_2601.16123v1_source_review.md`,
  SHA-256 `97a22d91f88b07512153b98141b4a03bfa02c56aa3d278030cf41b2014f90182`.
- The audit hash declared by the draft matches the reviewed audit exactly; its source hash matches
  the local and official PDF.
- Independent full-text and visual review covered all 18 pages, including Eqs. (1)--(8), Algorithm
  1, Figs. 1--7, Tables I--VIII, the appendix and the complete reference/availability boundary.

## Independent scientific reconstruction

### Task, record and calibration representation

The hardware task is a one-dimensional X- or Z-basis repetition-code memory experiment. For each
fixed basis, distance `d` and odd round count `r`, a dynamic circuit repeatedly measures and resets
`d-1` ancillas and then measures the data qubits. Consecutive stabilizer outcomes are XORed to form
an ordered `r x (d-1)` detector tensor.

The second decoder input is a target-chain heavy-hex graph built from a calibration snapshot. Node
and edge fields include `T1`, `T2`, readout assignment error, and one- and two-qubit gate error
information. This is supplied metadata about a slowly varying hardware snapshot; it is not an
inferred calibration trajectory, a persistent carrier state or a stochastic temporal transition law.

### Learned parameters versus effective weights

A three-layer GCN and global mean pool produce a 256-dimensional embedding. An MLP generates
layer-wise FiLM scales and shifts for a three-block convolutional decoder. The CNN consumes the
ordered detector tensor and returns per-data-qubit flip probabilities; thresholded outputs update a
Pauli frame before majority vote.

The distinction between two forms of “fixed” is load-bearing:

- training fixes the learned GCN, FiLM-generator, CNN and output-head parameters;
- each new target calibration graph changes the GCN/MLP output `(gamma,beta)`;
- in folded mode, those new values are algebraically absorbed into new effective convolution
  weights and biases for subsequent records.

Thus the later Kingston result uses fixed learned parameters but fresh target-conditioned effective
weights. It is not calibration-blind deployment of one numerically unchanged CNN.

### Training granularity and transfer domain

Shots from Fez, Kingston and Pittsburgh are pooled within each basis and `(d,r)`, then split 70:30.
A separate FiLM model and separate CNN are trained for every basis and every `(d,r)`. Kingston is
therefore a seen training device. The one-week-later test uses different contiguous Kingston chains
and new calibrations, so it supports source-reported transfer across chain selection and operating
snapshot within a seen device. It does not support leave-one-device-out, cross-device,
cross-distance, cross-round, cross-basis or cross-code transfer.

The 30% validation partition is used for checkpoint selection by validation accuracy and then for
the reported validation LERs. It is excluded from gradient training but is not an independent test
set for model-selection purposes. The later Kingston experiment is the stronger transfer test, though
the paper does not document target-data exclusion from all architecture/hyperparameter choices or
identify exact evaluated checkpoint hashes.

### Comparator and evidence strength

The unconditioned CNN preserves the convolutional backbone, detector input, loss, optimizer, split
and threshold while removing the graph encoder and FiLM generator. This is a substantially matched
neural-package comparison and isolates the incremental calibration-conditioning path more cleanly
than an unmatched decoder comparison. Parameter count, seed/repetition protocol, exact checkpoint
identities and paired-outcome uncertainty are not reported, so it remains a comparison between two
trained packages rather than a fully replicated causal component estimate.

The modified MWPM arm also receives current target calibration, but through a separately constructed
Pauli-twirled detector graph and edge weights for each device, basis, `(d,r)` and snapshot. FiLM
versus MWPM therefore does not isolate the mere availability of calibration metadata; FiLM versus
the matched CNN is the relevant conditioning contrast.

### Result pattern

The source reports a crossover: shallow circuits often favor MWPM or CNN, while FiLM gains
concentrate at larger `d` and `r`. Concrete counterexamples to universal superiority include:

- validation Z basis, `d=3,r=3`: FiLM `0.0116`, MWPM `0.0111`, CNN `0.0110`;
- later Kingston Z basis, `d=3,r=3`: FiLM `0.0171`, MWPM `0.0166`, CNN `0.0112`;
- later Kingston X basis, `d=3,r=1`: FiLM `0.00350`, MWPM `0.00256`, CNN `0.00248`.

At later-Kingston `d=11,r=11`, the printed values do support the audit's selected comparisons:

- Z basis: FiLM `0.00879`, MWPM `0.0652`, CNN `0.0733`, corresponding to approximately `7.42x`
  and `8.34x` from the printed LERs;
- X basis: FiLM `0.0540`, MWPM `0.118`, CNN `0.113`, corresponding to approximately `2.19x`
  and `2.09x`.

These are configuration-specific hardware results, not a universal decoder ordering.

### Uncertainty, latency and memory-law boundaries

The figures contain shaded 95% bands. The text calls them binomial confidence intervals, while the
unseen Fig. 6 caption calls them intervals across calibration snapshots. The paper gives neither a
single aggregation formula nor per-configuration shot counts or numerical endpoints. Consequently,
the evidence is stronger than bare point estimates but cannot support exact reanalysis, paired
decoder inference or a population-general significance claim.

Table I measures batch-one GPU forward passes after warmup: folded FiLM and CNN are approximately
81--98 microseconds, while dynamic FiLM is approximately 1.38--1.43 milliseconds. The benchmark
excludes record transport, control-stack integration, target-graph processing and weight-folding
update cost. The reported timing variation is over repeated forward passes, not evidence of an
end-to-end real-time QEC deployment.

Both neural arms receive the same multiround detector history. Their controlled difference is fresh
calibration metadata, not access to history or a declared memory state. The paper does not estimate
or misspecify a memory kernel, carrier lifetime, hidden transition or formal non-Markovianity.
Statements attributing deep-circuit behavior to “non-Markovian” or parasitic correlated errors, and
the Jacobian-based physical interpretations, are hypotheses/interpretations rather than measured
causal identifications.

## Operation replay

| input | transformation | critical assumption | output | cross-review result |
|---|---|---|---|---|
| Repetition-code dynamic circuit | Prepare basis state, repeat ancilla parity measurement/reset, measure data | Repetition code is the intended hardware testbed | Stabilizer outcomes and final data bits | **complete** |
| Consecutive stabilizer outcomes | `chi[t,i] = s[t,i] XOR s[t-1,i]`, with zero initial reference | Printed detector convention is used | Ordered detector tensor | **complete** |
| Target chain plus current calibration | Build node/edge-feature heavy-hex subgraph | Calibration snapshot is informative for the target records | Calibration graph | **complete; snapshot, not trajectory** |
| Calibration graph | Three GCN layers, mean pool, MLP | Learned mapping transfers within its training domain | FiLM scales and shifts | **complete** |
| Detector tensor plus FiLM values | Three modulated 3x3 CNN blocks and output head | Calibration modulation is the package-level treatment | Per-qubit flip probabilities | **complete** |
| Thresholded predictions and data readout | Pauli-frame XOR and majority vote | BCE target is prepared bit XOR measured bit | Corrected logical outcome and LER | **complete** |
| Pooled Fez/Kingston/Pittsburgh data within one basis and `(d,r)` | 70:30 split, Adam/cosine training, validation-accuracy checkpoint | Split grouping and target-blind selection are not fully documented | One FiLM and one CNN checkpoint per configuration | **method complete; validation is reused for checkpoint selection** |
| Same detector backbone/training protocol | Remove calibration encoder and FiLM generator | Remaining differences adequately define the neural ablation | Matched CNN package | **complete; seeds/checkpoint identities absent** |
| Calibration-derived Pauli model | Build new detector graph/weights per target snapshot and run MWPM | Pauli-twirled graph is a suitable algorithmic baseline | MWPM logical decision | **complete within declared approximation** |
| New Kingston chain and calibration one week later | Apply fixed learned mapping to fresh graph; fold new FiLM values; decode new records | Seen-device calibration embedding transfers to the new chain/snapshot | Later-Kingston LER rows | **complete; target-conditioned within-device transfer** |
| Calibration update | Dynamic per-record GCN/MLP or asynchronous folding | Calibration is slow relative to record decoding | Dynamic or folded inference path | **complete; update cost unmeasured** |
| Batch-one GPU input | 500 warmups and 2,000 timed forward passes | RTX 5000 timing represents relative neural overhead | Table I mean and SD | **complete only for offline forward-pass benchmark** |

Direct arithmetic from the printed tables reproduces the selected ratios. It does not reconstruct
confidence bands, population weighting or paired uncertainty because the required counts and
aggregation rule are absent.

## Claim-and-locator cross-check

| draft fact | source finding | result |
|---|---|---|
| `stein-source-identity` | Identity, date, authors and 18-page extent are correct. | **pass** |
| `stein-selection-scope` | Devices, repetition-code scope, multiround records and later Kingston chains are correct. | **pass** |
| `stein-repetition-task` | Scientific claim is correct. Figs. 2--3 are on p. 7, not the declared p. 3; retain both Sec. II.A p. 3 and p. 7 figure anchors if the figures are load-bearing. | **pass; improve locator** |
| `stein-detector-representation` | Eq. (2), convention and tensor shape are correct. | **pass** |
| `stein-calibration-graph` | Graph fields and snapshot interpretation are correct. | **pass** |
| `stein-film-computation` | Architecture, 256-dimensional embedding and output are correct. | **pass** |
| `stein-output-interface` | BCE target, threshold, Pauli-frame update and majority vote are correct. | **pass** |
| `stein-model-granularity` | Separate basis/`(d,r)` models and “single model” boundary are correct. | **pass** |
| `stein-training-protocol` | Optimizer, schedule, epochs, split and checkpoint criterion are correct. Add that the reported validation set is used for checkpoint selection. | **revise boundary** |
| `stein-matched-cnn-comparator` | The matched dimensions and removed calibration path are correct. Do not promote this to a history/memory-access contrast. | **pass** |
| `stein-mwpm-comparator` | Target-calibrated, per-snapshot construction is correct. | **pass** |
| `stein-experimental-reach` | Counts and code reach are correct. The exact total/snapshot statement is on p. 6; `PDF page: 7` is not the primary anchor. | **revise locator** |
| `stein-unseen-transfer-protocol` | No retraining/fine-tuning, new Kingston chains, later calibrations and seen-device boundary are correct. | **pass** |
| `stein-validation-result` | False: Tables III--IV contain numerous settings where FiLM is worse than one or both comparators. Rewrite around the reported crossover/large-system subset. | **revise claim** |
| `stein-unseen-transfer-result` | False: Tables V--VI do not show FiLM below both comparators in every row. Rewrite as configuration-dependent and retain exact selected rows. | **revise claim** |
| `stein-unseen-x-result` | Values and comparator-specific ratios are correct. | **pass** |
| `stein-uncertainty` | Confidence-band existence and the two inconsistent descriptions are correct. | **pass** |
| `stein-conditioning-modes` | Dynamic/folded distinction is correct, but the locator cites Table VII, which is the X-basis FiLM-mode SVD table. The relevant latency/mode table is Table I on p. 10. | **revise locator** |
| `stein-latency-result` | Values and non-integrated boundary are correct. | **pass** |
| `stein-transfer-boundary` | Fixed learned parameters versus fresh calibration, seen device and per-configuration model boundaries are correct. | **pass** |
| `stein-abstract-gain-inconsistency` | Correct: the `11.1x` row is validation Table III, not later Kingston Table V. Exact table anchors are pp. 14--15, not p. 2 alone. | **pass; broaden locator** |
| `stein-x-ratio-inconsistency` | Correct: Table VI resolves `2.19x` over MWPM and `2.09x` over CNN. Table VI is on p. 16. | **pass; broaden locator** |
| `stein-gap-memory-law` | Correct source-local absence. | **pass** |
| `stein-gap-memory-access` | Correct: both neural arms consume identical detector-history representation. | **pass** |
| `stein-gap-wrong-model` | Correct: no stale/missing/biased calibration or wrong temporal law is tested. | **pass** |
| `stein-gap-unseen-device` | Correct. | **pass** |
| `stein-gap-cross-configuration` | Correct. The positive separate-model statement is on pp. 2, 4 and 6 rather than p. 7. | **pass; improve locator** |
| `stein-gap-calibration-blind` | Correct. | **pass** |
| `stein-gap-validation-split` | Correct and load-bearing. Add validation-checkpoint reuse to the evidence boundary. | **revise boundary** |
| `stein-gap-uncertainty` | Correct. | **pass** |
| `stein-gap-data-locator` | Correct for the fixed PDF; no repository identifier, URL or data-availability section is present. | **pass** |
| `stein-gap-integrated-latency` | Correct. | **pass** |

## Audit-packet cross-check

The T1, F1, D1-memory, R1, M1, U1 and L1 distinctions are scientifically sound. Required audit
revisions are:

1. Correct the artifact declaration from PDF 1.5 to PDF 1.7.
2. Replace `D2: closed as a bounded population-level ... comparison` with a qualified
   multi-configuration hardware comparison. The printed design grid is complete, but the later
   target chain/snapshot population, selection/exclusion rule, cell counts, pairing and inferential
   aggregation are not defined.
3. State that the FiLM-versus-CNN benefit is configuration-dependent and concentrated beyond the
   reported crossover. It is not a benefit in every hardware configuration.
4. Add the validation-set checkpoint-selection boundary: the 30% partition is not used for gradient
   training, but it is used to choose checkpoints before its LER is reported.
5. Preserve the distinction between fixed learned parameters and calibration-dependent FiLM/effective
   convolution weights. The current audit handles this correctly.
6. Preserve the non-promotion from calibration conditioning to memory-conditioned benefit,
   microscopic attribution, strict non-Markovianity or wrong-memory-law robustness.

The operation replay in the audit is detailed and faithful. Its selected numerical rows replay, but
the source does not expose enough information to replay the confidence bands, target-population
weighting, exact trained checkpoints or calibration-update timing.

## Schema and relation audit

The ordinary artifact-verifying parser rejects the note at its intentional draft-status gate
(`unpersisted`, `draft_not_admitted`). A read-only body parse beyond that gate accepts all 32
sections because all 18 pages are declared visually checked and the locator strings are mechanically
valid. Scientific locator corrections listed above are still required.

All five relations fail:

1. `object_type = "representation"` is unsupported, and `target hardware calibration graph` does
   not occur verbatim in the linked Claim.
2. `GCN-conditioned FiLM convolutional decoder` does not occur verbatim in the linked Claim.
3. `unseen-chain later-snapshot transfer result` does not occur verbatim in the linked Claim; that
   Claim also requires scientific correction because its universal result is false.
4. `predicate = "compares_with"` is unsupported, and `matched unconditioned CNN comparator` does
   not occur verbatim in the linked Claim.
5. The final relation points to `stein-gap-memory-law`, a `literature_gap`; relations must point to
   `paper_fact` records. Its object label also does not occur in the Claim.

A mechanically valid candidate set, tested read-only in memory, is:

- relation 1: `object_type = "model"`, label `target contiguous heavy-hex qubit chain`;
- relation 2: label `three-layer graph convolutional network`;
- relation 3: label `one-week-later Kingston experiments`, after correcting the fact Claim;
- relation 4: `predicate = "defines"`, label `unconditioned CNN comparator`;
- relation 5: point to `stein-transfer-boundary` with a boundary object such as
  `stein-calibration-conditioned-transfer-scope` and label `fresh target calibration`.

With those hypothetical relation repairs, all 32 sections (22 `paper_fact`, ten `literature_gap`)
and all five relations pass the body/relation parser. Scientific claim corrections must precede any
metadata promotion.

## Required revisions before pass

### Audit

1. Correct PDF version to 1.7.
2. Downgrade population-level closure to a configuration-wide matched hardware comparison with
   undefined target population/selection and non-reconstructible uncertainty.
3. Make the FiLM benefit explicitly configuration-dependent.
4. Add validation-set checkpoint reuse to the evidence limitations.

### Draft note

1. Rewrite `stein-validation-result` and `stein-unseen-transfer-result` so they describe the
   crossover/large-system subset rather than universal table-wide superiority.
2. Add validation-checkpoint reuse to `stein-training-protocol` or
   `stein-gap-validation-split`.
3. Replace `Table VII` with Table I for conditioning modes and repair the page anchors for
   experimental reach, result tables and cross-configuration granularity.
4. Repair all five relations as above.
5. Retain the current fixed-learned-parameter versus fresh-calibration/effective-weight distinction,
   the seen-Kingston boundary, per-basis/`(d,r)` training, wrong-memory-law absence and latency
   exclusions.

## Disposition

- `read_status`: complete
- fixed-PDF identity/hash: **pass**
- audit/source-note hash binding: **pass**
- T1 within-seen-device, fresh-calibration-conditioned interpretation: **pass**
- FiLM/CNN matching: **pass with training/checkpoint uncertainty**
- universal validation/later-result Claims: **fail; revise**
- population-level closure: **revise to bounded multi-configuration evidence**
- uncertainty, latency and memory-law boundaries: **pass**
- relations/schema readiness: **revise**
- overall cross-review: **REVISE**
- manifest action: none taken

After revision, the strongest defensible use is: Stein et al. provide a substantially matched
hardware comparison showing configuration-dependent benefit from fresh calibration conditioning on
later, unseen Kingston chains while learned parameters remain fixed. The effective conditioned
weights are refreshed, Kingston is a seen training device, models are separate for every basis and
`(d,r)`, and neither wrong-memory robustness nor cross-device/cross-code transfer is demonstrated.

## Final revision verification

### Artifact and hash binding

- The official arXiv byte stream and fixed local PDF remain byte-identical: PDF 1.7, 18 pages,
  696,762 bytes, SHA-256
  `f09848cdf8ed099ebf213750bdbf397a92659f04c4e8c6e5177454821b3de50e`.
- The revised audit SHA-256 is
  `aa939b421cbfdc8dd3f18615ba4ecac16c1b56885f38a2269d1cea6779d07783`; the revised draft note
  declares that exact audit hash and the fixed-PDF hash above.
- The revised draft-note SHA-256 is
  `db8db7ae40d321fe2124fba4469264f7d9fd70f8d970592cdd9d6cbde91e21ab`.
- The note remains intentionally gated as `unpersisted` / `draft_not_admitted`, so the ordinary
  admission parser excludes it before inspecting the body. A read-only shadow parse that changes
  only those admission-state fields, while retaining artifact verification, accepts all 32 sections
  (22 `paper_fact`, ten `literature_gap`) and all five relations. This is a readiness diagnostic,
  not an admission action.

### Required-revision closure

| required revision | final verification |
|---|---|
| PDF version | Corrected to PDF 1.7 in the audit. |
| D2 evidence status | Downgraded to strong configuration-wide matched hardware calibration-conditioning evidence; target population, selection, cell counts, pairing and aggregation remain explicitly unresolved. |
| Result ordering | Both validation and one-week-later Claims now state configuration-dependent ordering. Independent replay of Tables V--VI gives 20 rows per basis and 14/40 strict FiLM wins over both comparators (Z: 8; X: 6). |
| Validation reuse | The note and audit now state that the 30% partition selects checkpoints before its LER is reported and is not an independent post-selection test. |
| Conditioning-mode locator | Corrected from Table VII to Table I, PDF p. 10. |
| Other locator repairs | Experimental reach is anchored to p. 6; table-result and ratio Claims include Tables III--VI on pp. 14--16; cross-configuration granularity includes pp. 2, 4 and 6. |
| Relations | All five now use supported predicates/types, verbatim Claim labels and `paper_fact` targets; artifact-verifying shadow parse accepts them. |

### Scientific non-regression

The revised packet retains every load-bearing boundary established by the initial review:

- learned GCN/FiLM/CNN parameters are fixed in the later Kingston test, but fresh target
  calibration produces new FiLM values and, in folded mode, new effective convolution weights;
- Kingston is a seen training device, and a separate model is trained for each basis and `(d,r)`;
  the result is therefore within-device, target-conditioned transfer, not unseen-device,
  cross-configuration, cross-code or calibration-blind transfer;
- the FiLM/CNN comparison is substantially matched at the neural-package level, while seeds,
  checkpoint identities, target-population definition, paired outcomes and reconstructible
  uncertainty remain absent;
- both neural arms consume the same ordered detector history, so the comparison establishes a
  calibration-conditioning contrast rather than memory-access benefit;
- no continuing carrier, temporal transition law, wrong-memory-model perturbation, causal
  microscopic attribution or formal quantum non-Markovianity is demonstrated; and
- latency remains an offline batch-one GPU forward-pass comparison, not end-to-end QEC control
  latency or a measured calibration-update cost.

Final disposition: **PASS for pre-admission review.** This supersedes the initial `REVISE` decision.
The requested scientific, locator and relation repairs are complete, with no new claim promotion.
No audit, draft-note or manifest file was changed by this final verification.
