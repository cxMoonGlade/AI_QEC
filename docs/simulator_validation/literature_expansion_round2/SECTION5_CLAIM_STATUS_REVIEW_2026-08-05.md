# Section 5 claim-status review after literature expansion round 2

## Scope

This review updates the Section 5 judgments in
[assessment 16](../../../outputs/researchwrite/qec-memory-directed-research-report/overview_rebuild/16_expanded_corpus_sections3_5_assessment.md)
using only the seven fixed-source round-2 audits and their source notes. It does not add literature,
adjudicate corpus admission or claim search exhaustion beyond this bounded source set.

The seven sources contribute different evidence objects:

| source | strongest Section 5 function | essential boundary |
|---|---|---|
| [Kurilovich et al.](KURILOVICH_ERROR_BURSTS_2506_18228_AUDIT_2026-08-05.md) | Simultaneous adjacent-region monitoring links selected QP-associated phase bursts to cycle-resolved repetition-code detector bursts; controlled detuning and echo test detector susceptibility | Monitor and QEC qubits are disjoint; natural events are not replayed across circuits; no logical-error or cross-device result |
| [Miao and McEwen et al.](MIAO_DQLR_2211_04728_AUDIT_2026-08-05.md) | Prepared leakage, measured lifetime and transport, targeted all-qubit removal, syndrome-correlation suppression and logical comparisons on hardware | The QEC arms differ in timing, operations and one detector convention; cost matching is XEB-only; broader event attribution is not established |
| [Remm et al.](REMM_SYNDROME_CORRELATIONS_2502_17722_AUDIT_2026-08-05.md) | Direct multicycle surface-code covariance and error-signature inference | The long tail has several viable causes; the correlated-decoder difference is not significant and is not a long-history ablation |
| [Nayak et al.](NAYAK_ITERATIVE_QP_DECODER_2603_18231_AUDIT_2026-08-05.md) | One model-matched synthetic comparison between online latent-QP estimation and a fixed uniform prior | Headline events are selected for large genie/uniform impact; proposed methods lack an all-event average, uncertainty and equal-compute control |
| [Bausch et al.](ALPHAQUBIT_RECURRENT_DECODER_2310_05900_AUDIT_2026-08-05.md) | Held-out experimental decoder performance, simulated soft/leakage-input gains and same-model long-round application | No matched history-access ablation; explicit soft/leakage comparisons are simulated; 25-to-100,000-round evaluation is not cross-setting transfer |
| [Manabe et al.](MANABE_LEAKAGE_MPS_2308_08186_AUDIT_2026-08-05.md) | Repeated-QEC qutrit-MPS simulation and matched modeled reset/removal comparisons | Simulation only; modeled removal operations have no physical duration, infidelity or calibration cost; geometry is one-dimensional or width 3 |
| [Marshall and Kafri](MARSHALL_KAFRI_STA_2312_10277_AUDIT_2026-08-05.md) | Exact-trajectory versus subspace-twirled leakage comparisons and model-conditioned logical consequences | Simulation only; no uniform approximation bound, memory-aware decoder, hardware attribution or transfer |

## Updated claim ledger

| analytical claim | assessment 16 | round-2 judgment | change from assessment 16 |
|---|---|---|---|
| **Observation of multicycle temporal structure** | Supported but sparse: a leakage-interpreted repeated-parity record and rare repetition-code detector events | **Supported across several, still selective hardware settings.** Remm directly resolves a distance-3 surface-code covariance tail through the plotted `Delta-m = 11` after post-selection. Kurilovich records selected cycle-resolved repetition-code bursts aligned with slowly decaying Ramsey bursts on an adjacent monitor region. Miao follows intentionally prepared leakage through multicycle surface-code circuits. | **Strengthened, but no categorical closure change.** Hardware support is broader than the two patterns summarized in assessment 16, including a direct surface-code covariance record. It still does not establish prevalence, one common mechanism or strict quantum non-Markovianity. |
| **Physical attribution** | Partial inside models; unresolved for unexplained hardware events | **Qualified mechanism-specific hardware attribution now exists.** Miao prepares leakage, measures its lifetime, transport and gate-conditioned pathways, and suppresses the predicted temporal structure with targeted removal. Kurilovich combines negative frequency shifts, Ramsey/echo discrimination, reciprocal recovery and excitation/relaxation hierarchy to support a QP-associated quasi-static frequency-shift pathway for a selected burst class. Remm's tail remains non-unique. | **Material status change.** Attribution is no longer only model-internal. The new support is restricted to prepared leakage and a selected QP-associated event class; it does not identify every burst, the initiating radiation species or the cause of Remm's long tail or the earlier unexplained Google events. |
| **Effect on multicycle or logical QEC quantities** | Supported in several bounded simulations and by hardware event–failure association | **Supported in bounded hardware and simulation settings.** Miao links prepared/persistent leakage and its removal to detector correlations and selected logical metrics. Kurilovich establishes detector-level susceptibility to a controlled frequency step. Manabe and Marshall show model-conditioned leakage effects and approximation dependence in repeated-QEC logical outputs. | **Strengthened, not reclassified.** The evidence now includes a hardware leakage intervention tied to downstream logical quantities, rather than only association plus simulation. No universal sign, scale, threshold shift or device prevalence follows. |
| **Benefit from a memory-aware decoder** | Strong claim missing; no matched active memory-aware decoder comparison | **One narrow synthetic positive contrast; general claim remains open.** Nayak holds selected event, code, two-cycle window, stride and BP+OSD backend fixed while replacing a uniform prior with online EKF field inference, lowering plotted PLE from 0.28 to 0.23 for the selected surface-code event and from 0.76 to 0.52 for the selected BB-qLDPC event. AlphaQubit demonstrates strong decoder performance but does not isolate history access; Remm's experimental correlated update is not significant and targets Pauli-Y cross-type information rather than the long tail. | **Example-level status change.** Assessment 16 had no matched positive instance. Round 2 supplies one selected-event, model-matched synthetic instance, but not a population-level, uncertainty-quantified, hardware or transferable benefit. The field-level claim remains unclosed. |
| **Benefit from carrier reset or physical control** | Active memory-aware control was absent; positive interventions were post-selection and drift adaptation | **Qualified mechanism-specific hardware benefit is supported.** Miao's DQLR actively removes the prepared leakage carrier and improves leakage, correlation and selected logical outcomes on common code tasks, with an XEB operation-cost measurement. Kurilovich's recentered dynamical decoupling plus echo reduces excess detector response to a controlled `-1 MHz` shift from 17 to 2 percentage points. Manabe supplies a modeled reset/removal cross-check. | **Material status change.** Section 5 should no longer say active physical intervention benefit is absent. It should say that leakage removal and phase-accumulation mitigation work in specific settings, while strict duration/record matching, cost-normalized logical benefit, natural-event replay and transfer remain unresolved. |
| **Robustness to finite data, approximation and model mismatch** | Open; available work showed limited diagnostics rather than robust deployment | **Partial diagnostics, no positive robustness claim.** Remm shows that finite samples, heterogeneity and pooled nonstationarity can erase or reverse an apparent decoder improvement. Marshall identifies regimes where a subspace-twirled approximation succeeds and a strong coherent-leakage regime where it fails. AlphaQubit shows pretraining-model sensitivity mitigated by experimental fine-tuning, and Nayak tests only a wrong uniform prior inside the assumed QP model. Miao and Kurilovich expose additional reset/calibration and event-selection boundaries. | **Status unchanged.** Failure modes are better characterized, but no source establishes robustness of a memory-aware inference or intervention to an incorrect carrier law, mixed noise, calibration error and distribution shift on held-out data. |
| **Transferability** | Not established | **Not established.** AlphaQubit's 25-to-100,000-round result stays within one distance-specific Pauli+ setting. Nayak tunes parameters separately for two codes and selects different events. Miao uses several tasks on one processor family; Kurilovich changes protected basis on one device; Manabe and Marshall separately instantiate multiple simulated codes. | **No change.** None freezes a calibrated representation, estimator, decoder or intervention and evaluates it on an independently held-out device, code family, mechanism or operating regime. |

## What Section 5 may now say

The round-2 evidence supports a more differentiated present-state judgment than assessment 16:

1. Multicycle temporal structure is observed in several superconducting repeated-QEC records, but
   the measured objects and selection procedures differ and none is a generic witness of quantum
   non-Markovianity.
2. Causal attribution is strongest when the candidate carrier is prepared or selectively probed and
   then targeted by an intervention. Prepared leakage satisfies that standard in one hardware line;
   a selected QP-associated phase-burst class has a convergent but indirect attribution chain.
   Unexplained covariance tails and rare detector bursts remain non-unique.
3. Temporal mechanisms can affect detector and logical quantities, but the demonstrated direction
   and magnitude remain conditional on mechanism, circuit location, code, decoder and finite tested
   regime.
4. Active physical mitigation is now supported for leakage removal and controlled phase-shift
   susceptibility. Memory-aware decoding has only one highly selected synthetic positive example;
   good performance by a recurrent decoder is not evidence that history access caused the gain.
5. Robustness and transfer remain the principal evidential gaps. More examples, longer horizons or
   separately tuned code instances do not substitute for a frozen cross-setting test.

## Non-promotion rules retained after round 2

- Do not promote a recurrent state, multicycle covariance, drift, leakage or a QP field into a claim
  of strict quantum non-Markovianity.
- Do not transfer Miao's prepared-leakage attribution to Remm's tail, Kurilovich's excluded box-like
  events or the earlier unexplained Google bursts.
- Do not call AlphaQubit's experimental advantage a memory-aware benefit: recurrence, architecture,
  training, input representation, fine-tuning and ensembling are not separated by a no-history
  control.
- Do not report Nayak's Fig. 6 as a 64-event average or as a statistically resolved hardware result.
- Do not call Remm's 0.004-percentage-point fitted difference a decoder benefit; the source states
  that it is not statistically significant and uses the same data for weights, interpolation choice
  and fidelity.
- Do not call Miao's or Kurilovich's intervention universally cost-effective: the strongest QEC arms
  are not fully duration- and record-matched, and Kurilovich's causal injection is detector-level.
- Do not promote approximation checks in Manabe or Marshall into robustness of a physical-memory
  estimator under device mismatch.
- Do not call same-model horizon extension, same-device basis variation or separately tuned code
  demonstrations transfer.

## Closure verdict

- `closure_status: open`
- Claims changed materially since assessment 16: qualified mechanism-specific hardware attribution;
  one narrow synthetic memory-aware decoder contrast; qualified active carrier-reset/control benefit.
- Claims strengthened without changing their high-level status: observation and bounded QEC
  consequence.
- Claims still missing: population-level or hardware memory-aware decoder benefit; systematic
  robustness to carrier/model misspecification; fixed-object cross-setting transfer; general
  microscopic attribution of unexplained hardware temporal structure.
- Allowed downstream action: write Section 5 as an asymmetrically weighted evidence synthesis using
  the updated bounded claims above. Do not write a mature-field, general-benefit, robust-transfer or
  search-exhaustion conclusion.
