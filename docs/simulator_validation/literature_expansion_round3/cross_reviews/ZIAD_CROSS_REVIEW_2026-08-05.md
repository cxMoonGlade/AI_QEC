# Independent cross-review — Ziad et al., DOI 10.1038/s41467-025-66773-x

## Decision

**REVISE.** The scientific disposition of D1, D2, R1 and T1 in the audit is substantially
correct, and none of the fixed artifacts should be rejected. The draft source note also passes the
current machine schema and all recorded hashes validate. It should nevertheless not be admitted in
its present form because several load-bearing page anchors are incomplete, one provenance sentence
overstates what the authors call proprietary, and the timing/resource language needs to distinguish
reported cycle-derived decoder-engine values from unmeasured end-to-end adaptivity.

No manifest, audit or source-note file was modified in this cross-review.

## Fixed-object verification

- Version of record: *Nature Communications* **16**, 11048 (2025), published 17 December
  2025, DOI `10.1038/s41467-025-66773-x`.
- Main PDF: 12 pages, 1,336,722 bytes, SHA-256
  `e245fe9a81ef635d9cda9421f416e27372aecb37b283d25d7951333a47428fa0`.
- Publisher Supplementary Information (`MOESM1`): 3 pages, 347,985 bytes, SHA-256
  `fde130c1e7418d800cd2ea462518de6dc3cea8a590251bf328e6f60c5f055b73`.
- Publisher peer-review file (`MOESM2`): 14 pages, 226,400 bytes, SHA-256
  `0968fbd4684aa4d7b6e38071123da2c2935b00eb48e4dd857e8175eb470dcec6`.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/ZIAD_LOCAL_CLUSTERING_DECODER_10_1038_S41467_025_66773_X_AUDIT_2026-08-05.md`,
  SHA-256 `8f0f9f5bd4c614593df7677019a0edd5b8d7a2b9f08381cea33b14a20ef97b7a`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/ziad_local_clustering_decoder_s41467_025_66773_x_source_review.md`,
  SHA-256 `2906acd1f16db52439b6035400af3ca044c9fe1d3cefb383b408aec6cb211877`.
- The note's embedded source and audit hashes match the fixed artifacts. Direct
  `parse_note(..., verify_artifact=True)` parsing succeeds with 24 evidence records and eight
  relations; the directory schema audit reports 20 `paper_fact` records and validates the note.
- Zenodo record `10.5281/zenodo.16982690` exposes four files. Local sizes and MD5 checksums match
  the official API, and the local SHA-256 values match the download manifest:

| file | bytes | official MD5 | local SHA-256 |
|---|---:|---|---|
| `fpag_performance_data.csv` | 3,426 | `417bab61640367c7a37ffedd99a73037` | `cc23f3a03a89976391a47966719a4fde7d460ff501663c7ddec08d6772d0a209` |
| `pymatching_comparison_circuits.zip` | 744,018 | `d31c790e1fade6d9f40be644d9672dc7` | `f3832816e1e7f4ad04ec6eba712e3ab92b32eb23203ad673a43dfb5da8effcdd` |
| `pymatching_comparison_results.csv` | 10,838 | `062cce10342abf8f73dcf566e67a9227` | `62c254881ddd3c8f5757b55f64552a1efd88aa12634e4e36a37f7a6dc28465ce` |
| `stim_circuits.zip` | 1,022,630 | `fe8c8db9336c3b02114ad2ba4b6b3ca6` | `f2de084d16c1625f08200957fb7eedddf038b45b12948e834a9c4a9bc77ab54d` |

Independent reading covered all 12 main-text pages, all 3 SI pages and all 14 peer-review pages.
Every page was rendered and traversed. Equations (1)--(2), Figs. 1--6, Supplementary Fig. 1,
Tables 1--4, Boxes 1--2 and the peer-review equation for edge support were checked visually.
Both CSV files and all ZIP member inventories were inspected; representative leakage-enabled and
leakage-free Stim circuits were opened directly.

## Independent scientific reconstruction

The simulated memory-bearing object is a classical leakage bit attached to each qubit in a modified
Stim Pauli-frame simulator. Leakage sets the bit, relaxation or reset clears it, and a leaked qubit
fully depolarises a sealed CZ partner. Patch wiggling resets every physical qubit within two rounds,
so a particular simulated leakage episode has a two-round maximum horizon. Measurement supplies a
noisy leakage herald with a false-negative channel.

The QEC-facing intervention is not a general learned history model. A herald addresses a
precomputed trigger-to-edge map. The adaptive arm supplies a set of affected existing edges as
pre-grown input to the same unweighted distributed LCD used by the non-adaptive arm; the latter
uses an empty pre-grown set. This is therefore a mechanism-specific side-information ablation.

The accuracy records are generated entirely by the modified simulator. The FPGA is the classical
decoder execution target, not the quantum-data source. The public leakage archive contains one
circuit definition for each of seven distances and two noise regimes, rather than separate circuit
definitions for the adaptive and non-adaptive arms. It contains aggregate counts but no individual
syndrome/herald records or seeds.

## Assigned-row findings

| row | independent source finding | disposition |
|---|---|---|
| D1 — hardware memory-conditioned decoder benefit | The same unweighted LCD construction is run with or without leakage-herald-derived pre-grown edges under a continuing two-round leakage process. This is a real decoder-hardware intervention on FPGA, but all QEC and herald records are synthetic. | **qualified closure only for FPGA decoder execution on simulated records; quantum-hardware-record benefit remains missing** |
| D2 — common-task population comparison | The archive has 14 common leakage circuit definitions: seven distances times two regimes. Each adaptive/non-adaptive arm has ten million shots, and adaptive failures are lower in all 14 matched configurations. This is population-wide and common-task/common-generator at the distribution level. The source does not establish identical per-shot record reuse, paired seeds or the `Lambda` fit/uncertainty method. | **closed as a common-task population comparison; qualified, not closed, under an additional identical-record/paired-uncertainty requirement** |
| R1 — wrong-memory-model robustness | Low- and high-leakage settings remain inside one matched SI1000-plus-leakage representation. False-negative heralding is included at the declared rate, but no stale/wrong lifetime, partner channel, herald calibration or mixed mechanism is deliberately imposed. | **missing** |
| T1 — frozen transfer | Distances are separately compiled from their decoding graphs; the two FPGA families establish implementation portability, not transfer of one frozen physical model/adaptation. No independent quantum device, code family or carrier law is a target domain. | **missing** |

These findings support the audit's core row statuses. They also settle the requested common-task
question: lack of identical-shot pairing is a statistical limitation, not a reason to call the
comparison event-selected or non-population-level.

## Population and evidence-boundary checks

- `fpag_performance_data.csv` has 28 data rows: adaptive and non-adaptive LCD at seven distances
  and two leakage regimes. Every row has 10,000,000 shots.
- There are 14 leakage circuit files, one for each distance/regime task. The same task definition is
  therefore available to both decoder arms even though the archive does not prove reuse of the same
  random draws.
- Adaptive failures are lower in all 14 arm-matched configurations. At distance 17 they are
  11 versus 2,835 in high leakage and 24 versus 139 in low leakage.
- Figure 3 reports `Lambda` values and rounded numerical uncertainties, but neither the article, SI,
  peer-review file nor archive gives the fit range, likelihood/weighting, resampling procedure or
  confidence interpretation. The raw aggregate counts support an independent analysis, not exact
  replay of the source's printed uncertainties.
- The leakage-free PyMatching comparison is a second population benchmark with 77 configurations
  per decoder and two million shots per row. It validates the base decoder under a different,
  non-wiggling depolarising task; it does not strengthen D1 or R1.

## Synthetic data versus quantum hardware

The audit and note correctly preserve the decisive boundary:

- **Quantum process and records:** modified-Stim simulation, including leakage state, relaxation,
  partner depolarisation, measurements, herald errors and logical outcomes.
- **Classical execution hardware:** Xilinx XCVU19P and ZCU111 FPGA implementations of LCD.
- **Not demonstrated:** decoder benefit on syndrome/herald records acquired from a quantum
  processor, causal validation of the simulated leakage channel on a device, or transfer of the
  adaptation to a different physical carrier.

Consequently, downstream prose may say “FPGA-executed population comparison on synthetic leakage
records.” It must not say “quantum-hardware memory-conditioned decoder benefit,” “device-demonstrated
leakage attribution” or simply “hardware data” without naming which hardware produced which data.

## FPGA timing, resources and extrapolation

The timing table is arithmetically reproducible from the public CSV. For distance 17, summing the
reported average initialising/growing/merging/picking/syncing cycle counts and dividing by distance
and clock frequency reproduces Table 3:

| arm/regime | average cycles per window | at 285 MHz XCVU19P | at 235 MHz ZCU111 |
|---|---:|---:|---:|
| non-adaptive LL | 2,228.0624 | 0.459868 microseconds/round | 0.557713 microseconds/round |
| non-adaptive HL | 3,011.3370 | 0.621535 | 0.753776 |
| adaptive LL | 3,087.6212 | 0.637280 | 0.772871 |
| adaptive HL | 3,277.0678 | 0.676381 | 0.820292 |

These values are decoder-state-machine cycle results combined with implemented/synthesised FPGA
clock frequencies. They are not a measured streaming trigger-to-correction latency. The article
explicitly excludes adaptivity-engine execution time, and the peer-review response's expectation
that it can be pipelined is not a measurement.

Tables 1--2 give one resource total per distance. They do not provide adaptive-versus-non-adaptive
resource rows or separately identify the storage/control cost of the adaptivity engine. The source
therefore supports total LCD implementation resource counts, not a measured incremental resource
cost for adaptivity.

The high-leakage `d=33` non-adaptive versus `d=17` adaptive comparison is based on extending the
fitted `P_L proportional Lambda^(-d/2)` trend to a target `10^-6` error probability for a
`d x d x d` window. Direct simulation, FPGA implementation and timing stop at distance 17. The
abstract's “one million error-free quantum operations” is therefore operational shorthand for this
target/extrapolation, not an execution of one million logical operations without failures.

## Source-note claim and locator audit

| fact or gap | semantic finding | locator/hash finding | result |
|---|---|---|---|
| `ziad-source-identity` | Correct. | Main/SI/peer page 1 and all three hashes verified. | **pass** |
| `ziad-selection-scope` | Correctly identifies simulated repeated-QEC records and FPGA decoding. | Page 1 is a valid primary anchor. | **pass** |
| `ziad-leakage-register` | Claim is correct. | Page 8 only introduces the representation; persistence, relaxation and reset details occur across main pp. 9--10. The locator should name those numbered items and use a load-bearing page anchor containing the claimed state transition. | **revise locator** |
| `ziad-patch-wiggling-horizon` | Correct. | Main p. 3 and SI pp. 1--2 support it. | **pass** |
| `ziad-leakage-partner-channel` | Correct within the declared Pauli-frame approximation. | Numbered items 1--4 and Table 4 span pp. 9--10; page 9 alone does not contain relaxation, reset and the table. | **revise locator** |
| `ziad-herald-channel` | Correct, including asymmetric false-negative-only parameterisation. | Main p. 10 is correct. | **pass** |
| `ziad-decoder-inputs` | Correct. | Main p. 6 is correct. | **pass** |
| `ziad-adaptivity-map` | Correctly preserves the difference between the broad precomputation description and the SI's simpler previous-reset approximation. | The locator should explicitly retain main pp. 4 and 10 plus SI p. 2; a page-4-only anchor does not locate the zero-weight equivalence. | **revise locator** |
| `ziad-decoder-computation` | Correct. | The detailed four-stage computation and Boxes 1--2 are on main pp. 6--7, not page 3. | **revise locator** |
| `ziad-population-comparison` | Correct and supported by all 28 aggregate rows. | Ten-million-shot language is in the Fig. 3 caption on main p. 5; page 4 is not the correct primary anchor. | **revise locator to p. 5** |
| `ziad-high-leakage-result` | Exact printed values and archived failure counts are correct. | Exact `Lambda` uncertainty is in the Fig. 3 legend on p. 5, not p. 4. | **revise locator to p. 5** |
| `ziad-low-leakage-result` | Exact printed values and archived failure counts are correct. | Exact `Lambda` uncertainty is in the Fig. 3 legend on p. 5, not p. 4. | **revise locator to p. 5** |
| `ziad-lambda-fit-boundary` | Correct and important. | Eq. (1) is on p. 3 and printed fit values are on p. 5; the locator should anchor the latter as well. | **revise locator** |
| `ziad-footprint-projection` | Correctly labels `d=33` as extrapolated and `d=17` as the direct reach. | Main pp. 4--5 support it. | **pass; broaden locator if edited** |
| `ziad-fpga-timing` | Numerical values are correct. “Measured” is too strong because the public chain is average stage cycles divided by implementation clock frequency. | Exact Table-3 values are on p. 9; p. 5 gives only the summary/Fig. 3. | **revise wording and locator** |
| `ziad-adaptivity-timing-boundary` | Correct: adaptivity-engine execution is excluded. | Main p. 5 is exact. | **pass** |
| `ziad-fpga-resources` | Counts and percentages are correct. The claim appropriately avoids an adaptivity-specific overhead. | Exact XCVU19P and ZCU111 counts occur on pp. 8--9; page 5 is only a summary. | **revise locator** |
| `ziad-pymatching-comparator` | Correct and correctly excluded from leakage-benefit evidence. | Threshold prose is on p. 7 and Fig. 6 on p. 9. | **pass** |
| `ziad-partner-channel-boundary` | Correct and strongly supported by the author response. | Main p. 10 plus peer-review pp. 6--8 are appropriate. | **pass** |
| `ziad-artifact-boundary` | The concrete archive boundary is correct, but the sentence says the modified Stim fork itself “remain[s] proprietary.” The authors say only that some simulation artifacts are proprietary; the archive inspection establishes that the modified Stim code and RTL are absent, not which absent component carries that label. | Main p. 10, Zenodo inventory and peer-review pp. 1, 8, 10 and 12 support the narrower formulation. | **revise wording** |
| `ziad-gap-quantum-device-records` | Correct. | Source-wide absence is properly scoped. | **pass** |
| `ziad-gap-identical-record-pairing` | Correct. | Fig. 3 and archive inventory support it. | **pass** |
| `ziad-gap-wrong-model-robustness` | Correct. | Main model plus peer-review countercondition support it. | **pass** |
| `ziad-gap-frozen-transfer` | Correct. | Discussion, hardware tables and peer-review response support it. | **pass** |

## Audit-packet review

The audit's hashes, source identity, D1/D2/R1/T1 statuses, synthetic/hardware split, partner-channel
countercondition, exact failure counts, FPGA table values and extrapolation warning all pass.

The following audit edits are required before admission:

1. Replace “with the extra decoder-engine time and FPGA resources reported” in Project application
   with wording that separates the reported adaptive cycle cost from total implementation resources;
   no incremental adaptivity-engine resource result is tabulated.
2. Describe Table-3/Fig.-3 timing as reported cycle-derived decoder-engine time, not unqualified
   end-to-end measured latency.
3. Reconcile `operation_replay_status = "complete"` in the source note with the audit row that says
   replay is incomplete for the `Lambda` fit/uncertainty procedure. A defensible resolution is to
   state that replay is complete through circuit generation, aggregate failure counts and timing
   arithmetic, while the published `Lambda` estimator and uncertainties remain explicitly
   non-replayable source-local outputs.
4. Preserve the current `d=33`/one-million-operation kill condition; it is correct and load-bearing.

## Required disposition

- `read_status`: complete
- cross-review result: **revise**
- audit scientific row judgments: pass
- source-note semantic fidelity: revise in two phrases plus page anchors
- provenance/hash integrity: pass
- machine schema: pass, but semantic replay-status reconciliation required
- manifest action: none taken; do not admit until the listed revisions receive a fresh hash/schema
  check

After those revisions, the source is suitable evidence for a carrier-specific, population-level
decoder-side benefit on synthetic leakage records with FPGA execution. It cannot support
quantum-hardware-record benefit, wrong-memory-model robustness, frozen cross-device/cross-code
transfer, end-to-end sub-microsecond adaptivity, measured incremental adaptivity resources, or a
directly executed distance-33/million-operation result.

## Revision verification

**Result: REVISE.** The requested scientific and locator revisions pass, but the revised source
note fails the admission schema at its relation labels. No manifest or source-note change was made
during this verification.

### Verified revisions

- Audit SHA-256 changed from
  `8f0f9f5bd4c614593df7677019a0edd5b8d7a2b9f08381cea33b14a20ef97b7a` to
  `b1de4a36e3d662fe4408a1c7b2153372b162c6378813b6c12a29e3055a0ffed6`.
- Revised source-note SHA-256 is
  `4aff208adff13488fa9237d9f6f66268f2e9947550507b59b37cb1cb5df35de0`, and its embedded
  `audit_packet_sha256` exactly matches the revised audit.
- The fixed main-PDF SHA-256 remains
  `e245fe9a81ef635d9cda9421f416e27372aecb37b283d25d7951333a47428fa0`.
- All requested load-bearing locators are now adequate: the leakage state-transition span is pp.
  8--10; the adaptation locator explicitly includes main pp. 4 and 10 plus SI p. 2; decoder
  computation points to pp. 6--7; the population and `Lambda` results anchor p. 5; exact timing and
  resource tables anchor pp. 8--9.
- Timing is now correctly defined as state-machine cycle averages divided by code distance and
  implementation clock frequency. Both documents retain the exclusion of adaptivity-engine and
  end-to-end streaming timing.
- Adaptive decoder-cycle cost, total implementation resources and the unmeasured incremental
  adaptivity-engine resource cost are now separated.
- The artifact statement now records absence of modified-Stim source, RTL/implementation source
  and raw records while attributing only the authors' generic “some artifacts are proprietary”
  statement. It no longer asserts that a named absent component is proprietary.
- The audit now explains that `operation_replay_status = "complete"` covers task/circuit
  reconstruction, aggregate counts and timing arithmetic, while the undocumented `Lambda`
  fit/uncertainty output remains non-replayable.
- `git diff --check` reports no whitespace errors for the audit, source note or cross-review.

### Remaining schema blockers

`parse_note(..., verify_artifact=True)` and the directory schema audit fail at relation index 5:

```text
relations[5] object_label must occur in the fact claim
```

The revised timing relation uses `object_label = "cycle-derived decoder-engine time"`, but the
corresponding Claim contains the exact phrase `reported decoder-engine times`, not the object label.
Use an exact Claim phrase as the label, or place the chosen label in the Claim.

The same mechanical mismatch remains in the final relation and will become the next failure after
relation index 5 is fixed: `object_label = "parts of the implementation"` no longer occurs in the
revised artifact-boundary Claim. An exact supported replacement is `RTL/implementation source` or
`modified Stim source`.

After those two relation-label corrections, rerun artifact-verifying `parse_note`, the directory
schema audit, SHA-256 recording and `git diff --check`. No further scientific or locator revision is
required by this verification.

## Final revision verification

**Result: PASS.** The two remaining relation labels now use exact phrases from their linked Claims:
`reported decoder-engine times` and `RTL/implementation source`. The changes are mechanical and do
not alter the scientific content or the evidence boundaries approved above.

Final verified hashes:

- fixed main PDF:
  `e245fe9a81ef635d9cda9421f416e27372aecb37b283d25d7951333a47428fa0`;
- revised audit:
  `b1de4a36e3d662fe4408a1c7b2153372b162c6378813b6c12a29e3055a0ffed6`;
- revised source note:
  `2cd62446c048452e77a19f0a0c5b2133f50bddbab263c09d904d01cbee38f226`.

Artifact-verifying `parse_note` succeeds with 24 evidence records and eight relations. The full
draft-directory schema audit lists the Ziad note as validated with 20 `paper_fact` records, the
expected source identity and the hashes above. `git diff --check` reports no whitespace errors.

Final disposition:

- source-note semantic fidelity: **pass**;
- audit semantic fidelity: **pass**;
- D1/D2/R1/T1 and synthetic-versus-quantum-hardware boundaries: **pass**;
- timing/resource/extrapolation qualifications: **pass**;
- artifact/hash integrity: **pass**;
- admission schema: **pass**;
- manifest action in this cross-review: none.
