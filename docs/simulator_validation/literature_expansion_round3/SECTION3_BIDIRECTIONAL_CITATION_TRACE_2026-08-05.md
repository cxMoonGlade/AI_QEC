# Bidirectional citation trace for the six Section 3 approach bundles

## Question and method

This trace tests whether backward references or later citing papers contain an equal or more
representative **complete repeated-QEC approach bundle** than any of the six rows proposed for the
overview matrix. A complete bundle must identify (i) what carries temporal dependence, (ii) the
QEC-facing object, (iii) the computation actually used, and (iv) a demonstrated repeated-QEC
output. A source is not promoted merely because it is more cited, newer, broader in generic QEC,
or better at a different task.

The audit used the fixed full texts and reference lists already reviewed for all six sources,
OpenAlex work/reference/citing-work records queried on 2026-08-05, exact-title web searches, and
direct inspection of candidate primary sources. Citation counts are discovery aids, not evidence.
Semantic Scholar's API returned rate-limit errors during this pass, so no negative conclusion rests
on that index. Very recent 2026 sources have incomplete forward-citation indexing; their forward
traces are recorded as immature rather than as proof of no neighbors.

## Result

| row | backward-chain result | forward-chain result | representativeness decision |
|---|---|---|---|
| **A1 — Kam, pair/streak event masks** | Earlier work covers correlated-error thresholds, adaptive decoding, time-correlated fault-tolerance and process-tensor foundations, but the reviewed references do not supply the same repeated-surface-code contrast with matched one-location marginals and explicitly varied joint temporal structure | OpenAlex reports seven citing works. They concern calibration tracking, device benchmarking, bosonic/random-telegraph noise, non-Markovian suppression or cosmic-ray-event mitigation; none implements an equal matched pair/streak repeated-QEC comparison | **Retain.** It remains the clearest controlled phenomenological contrast; it is not a device model or a general theory of correlated noise |
| **A2 — Kam, twirled QCA to PCA/HMM** | The paper explicitly builds on process tensors, multi-time Pauli twirling, QCA/PCA/HMM theory, the A1 surface-code comparison, Remm and the single-round Kobayashi tester. None of these predecessors provides the same constructed bath-to-effective-process-to-repeated-QEC bundle | The March 2026 preprint is not reliably indexed for forward citations. Exact-title searches found the source itself and summaries, not an independent equal bundle | **Retain provisionally.** It is the strongest physical-to-effective bridge in the current corpus, but its novelty and reach should be described as preprint-bounded, not field-wide dominance |
| **A3 — Manabe, full-system qutrit MPS** | Darmawan–Poulin tensor-network work has broader two-dimensional surface-code geometry under other noise assumptions, while earlier leakage studies have stronger experimental grounding. Neither combines persistent qutrit leakage, sampled multicycle branches and the reported large repetition/thin-surface-code reach | The only indexed citing QEC source is Ziad's local-clustering decoder; it uses leakage information for decoding rather than replacing the qutrit-MPS computation. A later neutral-atom erasure-tolerance paper is adjacent, not the same bundle | **Retain.** Its role is a concrete persistent-leakage computation, not “the” tensor-network approach |
| **A4 — Marshall–Kafri, full-qutrit trajectories plus STA** | Prior leakage simulation, density-matrix and mitigation papers do not provide the same exact-within-declared-model versus subspace-twirled trajectory comparison over repeated surface-code circuits. Manabe is an important complementary tensor-network route, not a duplicate | OpenAlex lists no citing works under the published DOI at the audit date. Exact searches found applications/mitigation neighbors but no stronger repeated-QEC exact-versus-STA comparison | **Retain alongside A3.** The two rows answer different questions: scalable retained-system propagation versus a controlled full-qutrit/surrogate approximation comparison |
| **A5 — Remm, hardware-record signature inversion** | Earlier syndrome-correlation calibration, adaptive weight estimation and decoder-prior optimization infer simpler or more static error information. They do not reproduce Remm's selected multicycle signature inversion and long-lag hardware-record analysis | Later work includes reconstruction of detector error models and Takou et al.'s syndrome-estimated DEM evaluation on Google and IBM data. Takou directly cites Remm and gives broader hardware prior-to-logical evaluation, but it does not replace Remm's long-lag/signature analysis; neither source defines a continuing carrier-state transition law | **Retain, but narrow its function.** Use Remm for memory-relevant record structure and non-attribution; use Takou in Section 5 as the stronger adjacent record-to-prior/logical-evaluation bundle |
| **A6 — Nayak, latent QP field plus DEM/BP+OSD** | The backward chain contains radiation/QP transport, correlated-noise characterization and generic BP/OSD decoding, but no earlier source jointly infers a continuing spatial QP field from syndromes and feeds it back into repeated-QEC priors | The March 2026 preprint has no mature forward-citation chain. Exact-title searches found the source and secondary discovery pages, not an independently demonstrated replacement | **Retain with severe evidence limits.** It is unique in the corpus as an explicit field-conditioned decoder bundle, while its reported algorithm gains remain selected-event, synthetic and uncertainty-free |

## Candidate-level decisions

### Earlier or adjacent sources not promoted to a main row

- **Correlated-error threshold/statistical-mechanics studies** establish formal sensitivity or
  thresholds, but generally do not return the same representation–interface–computation–reach
  bundle for a repeated circuit and an observed ordered record.
- **Darmawan–Poulin tensor-network surface-code simulation** is broader in code geometry than
  Manabe, but it does not carry the same persistent qutrit leakage state and multicycle leakage
  intervention comparison. It remains useful context for computational reach.
- **Leakage HMM and hardware leakage-detection studies** connect records to a hidden label or
  intervention, but adding them as extra rows would duplicate the leakage question without
  replacing either the MPS or trajectory comparison.
- **Calibrated/adaptive decoder-weight studies** are important Section 5 comparators. Static or
  snapshot-conditioned priors are not automatically temporal-memory representations.
- **Takou et al., arXiv:2606.11496**, is the most consequential A5 neighbor. It broadens
  syndrome-estimated DEM evaluation across released Willow data and new IBM data, but its model is
  re-estimated per instance and is not a long-history carrier model.
- **Ziad et al.**, **Stein et al.**, **QAdapt**, **Transformer-QEC** and the **AI loss decoder**
  chiefly test decoder execution, conditioning, training or transfer. They belong in the evidence
  synthesis unless a specific temporal representation is being compared; neural recurrence alone
  is not a physical memory-bearing representation.

## Coverage judgment

No traced source displaces one of the six rows on the scientific question that row is meant to
answer. The citation pass therefore supports keeping the six-row ceiling, with two qualifications:

1. The matrix is a **comparison of selected concrete bundles**, not a taxonomy or a claim that the
   rows exhaust the literature.
2. A5 must no longer carry the whole record-to-model evidence story. Remm remains the
   memory-relevant long-lag/signature example, while Takou supplies a broader adjacent test of
   syndrome-derived priors on hardware records.

The two very recent rows A2 and A6 have immature forward traces. Their retention is justified by
their distinctive source-local operations, not by a negative claim that no equivalent future or
unindexed work exists.
