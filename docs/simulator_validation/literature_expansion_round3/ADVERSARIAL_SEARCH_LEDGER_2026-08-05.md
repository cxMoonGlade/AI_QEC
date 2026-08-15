# Adversarial coverage ledger for decoder benefit, robustness and transfer

## Scope

This pass attempted to overturn four load-bearing negative or weak judgments in the repeated-QEC
memory overview. Searches deliberately used terms employed by adjacent communities rather than
only `memory-aware`: history/recurrent/temporal/context-conditioned, leakage/loss-aware,
noise/calibration/hardware-conditioned, adaptive/online, mismatch/robustness/drift/OOD, zero-shot,
transfer/generalization, cross-device, cross-distance and cross-code.

Discovery combined the current local corpus and its RAG/KG indexes, arXiv/exact-title web search,
OpenAlex reference and citing-work chains, source bibliographies, and targeted full-text acquisition.
Abstracts and snippets were used only to select candidates. Every row-changing result below is
based on a fixed full text with exact source-local boundaries.

## Sources pressure-tested

| source | fixed-source review | adversarial role | row effect |
|---|---|---|---|
| **Ziad et al., local clustering decoder** | VOR main text, SI, peer-review history and released Zenodo tables | strongest candidate for hardware leakage-conditioned decoding and population comparison | establishes decoder **hardware execution** and a large synthetic population comparison, but the QEC records are modified Stim records, not quantum-device records; no wrong-model or transfer test |
| **QAdapt** | official arXiv v1 full text | strongest claimed zero-shot simulation-to-Willow pre-decoder transfer | reports one external-Willow evaluation without target-domain update or calibration; strict target-unseen selection is not auditable, the comparator is not matched, LER uncertainty is absent and no temporal-memory law is isolated |
| **Hockings et al.** | official arXiv v2 full text | strongest calibration/noise-aware mismatch and broad-population neighbor | establishes a broad synthetic comparison under static heterogeneous Pauli calibration, with fixed-seed record pairing explicit in one distance-25 table rather than the whole sweep; not temporal memory, hardware benefit or frozen transfer |
| **Stein et al., calibration-conditioned FiLM** | official arXiv v1 full text | later-snapshot hardware transfer and matched conditioning ablation | establishes fixed-learned-parameter, target-calibration-conditioned transfer to new chains/later snapshots on a seen IBM device, plus a matched calibration-conditioning comparison; not memory-access ablation or leave-one-device-out transfer |
| **Yan et al., neural decoder reassessment** | official arXiv v1/ICML manuscript, including appendices | zero-shot hardware application and rate-shift robustness | establishes target-calibrated synthetic-pretraining to matched Sycamore records and fixed-checkpoint lower-rate tests inside two separately trained generator families; not cross-model, cross-device or memory-law transfer |
| **Molavi et al., decoder analysis** | official arXiv v1 full text | direct adversarial hit for “decoder robustness” | gives sound small-instance worst-case bounds over independent physical-rate hyperrectangles; does not perturb temporal dependence or a memory model |
| **Takou et al.** | official arXiv v2 full text | broad hardware record-to-prior-to-logical comparison and A5 forward neighbor | syndrome-derived DEM priors improve decoded LER on released Willow and new IBM data, but the model is re-estimated for each instance and no history/state ablation isolates memory |
| **Transformer-QEC** | official arXiv v1 full text | claimed cross-distance transfer | target distances receive ten epochs of fine-tuning plus positional adjustment; no frozen transfer, population specification or uncertainty |
| **Wang et al., AI-enabled loss decoder** | official arXiv v2 full text including embedded supplement | persistent-loss history and decoder-benefit candidate | useful synthetic demonstration that an absorbing loss state leaves multicycle flicker; no hardware, matched history ablation, sample count/uncertainty, wrong-model test or transfer |
| **AlphaQubit** | already admitted complete source review | long-record recurrent hardware decoder candidate | hardware performance is real, but no no-history/history-window comparator isolates temporal-memory access |
| **DGR** | existing fixed-source audit | history-reweighted versus static MWPM candidate | closest matched decoder-side history comparison in the prior corpus, but static edge mismatch and correlated-edge changes prevent a one-factor memory-access interpretation |
| **Nayak et al.** | already admitted complete source review | explicit latent-memory decoder benefit | all-event results compare genie and uniform priors; proposed inference algorithms are shown on selected events without uncertainty or equal compute |

## Row decisions

### D1 — hardware memory-conditioned decoder benefit

**Result: not closed.** The pass found three different positive claims that must not be collapsed:

- AlphaQubit and Yan et al. decode experimental multicycle records, but lack a comparator that
  changes only access to record history or a declared memory state.
- Stein et al. isolate access to current calibration metadata with a matched CNN comparator. That is
  hardware calibration conditioning, not temporal-memory conditioning.
- Ziad et al. implement an adaptive leakage-aware decoder on FPGA hardware, but evaluate synthetic
  leakage records rather than quantum-device records.

The corpus therefore supports hardware **record-aware**, **calibration-conditioned** and
decoder-hardware-execution examples, but no source reviewed here combines quantum-hardware
records with a logical metric and a matched ablation of access to a declared temporal-memory
state/history.

### D2 — population-level matched decoder comparison

**Result: partially closed, with more than one evidence level.**

- Ziad et al. use 10 million synthetic shots per arm across reported distances and provide fitted
  suppression uncertainty. This is a qualified population-level common-generator comparison, but
  strict identical-record/seed pairing is not stated and raw records are not released.
- Stein et al. provide the cleanest configuration-wide matched **calibration-conditioning**
  comparison: common CNN backbone, records, loss, optimizer, split and threshold, with
  later-snapshot hardware results and plotted confidence bands. The ordering is
  configuration-dependent, the validation partition also selects checkpoints, and the target
  chain/snapshot population and selection rule are not defined. It does not isolate temporal-memory
  access or close a population-level claim.
- Hockings et al. provide a broad static-calibration analogue; fixed-seed pairing is explicit for
  one distance-25 comparison rather than the entire sweep.
- QAdapt spans its reported Willow/synthetic settings but changes decoder architecture, parameter
  count and training, and omits LER uncertainty.
- Yan et al. report hardware comparisons and state a 5,000-shot test allocation per selected
  setting, but exact cohort reuse and aggregation are unstated; they select the lowest-baseline d=3
  center and omit hardware uncertainty.

Thus a blanket “no population comparison” is no longer defensible. What remains missing is a
strict population-level, common-record, uncertainty-bearing comparison that changes only
temporal-memory information or model use.

### R1 — robustness under a wrong memory model

**Result: not closed; adjacent robustness evidence is now positive.**

- Molavi et al. certify worst-case LER bounds over independently varying Bernoulli rates.
- Yan et al. freeze a checkpoint while lowering one scalar error rate inside the same generator
  family.
- Stein et al. apply fixed learned parameters at a later hardware snapshot while supplying fresh
  calibration metadata.
- Hockings tests static calibration/model mismatch.
- QAdapt reports OOD behavior across static Pauli settings.

None deliberately misspecifies a carrier lifetime, hidden-state transition, temporal kernel,
history length, herald reliability, mixed memory mechanism or stale memory estimate while holding
the intervention protocol fixed. Section 5 should therefore distinguish **rate/calibration
robustness**, which has bounded examples, from **wrong temporal-memory-law robustness**, which was
not demonstrated in the reviewed set.

### T1 — frozen transfer

**Result: the old blanket negative judgment is overturned, but the requested strong transfer is not
established.**

- QAdapt: source-reported application to Willow without target-domain fine-tuning, parameter update
  or calibration; exact checkpoint identity, target exposure during selection and cohort filtering
  are not documented.
- Yan et al.: fixed device-calibrated synthetic-pretrained TCN applied to the corresponding
  Sycamore hardware test records.
- Stein et al.: fixed learned parameters applied to new chains and later calibration snapshots on
  a device already represented in training; fresh target calibration changes the effective FiLM
  weights.
- Transformer-QEC does not add a frozen result because the target distance is fine-tuned.

These are bounded no-target-update, zero-shot or fixed-parameter applications with different
target-exposure boundaries. None demonstrates one frozen
memory-bearing representation, estimator or decoder across an independent device, code family
or memory mechanism without target-specific calibration, retraining or retuning. Cross-device and
cross-code T1 therefore remain missing.

## Search failures and exclusions

- Generic web searches for `memory-aware decoder` were dominated by computer-memory hardware,
  classical coding and secondary pages; exact QEC variants were required.
- Commercial or secondary claims of a universal graph-transformer decoder were not admitted
  without a fixed primary scientific artifact and demonstrated repeated-QEC transfer.
- Cross-distance neural architectures were not treated as cross-code or cross-device transfer.
- `Robustness` in a title or abstract was not enough: static rate intervals, ordinary calibration
  drift and OOD Pauli tests were retained as adjacent evidence, not promoted to wrong-memory-law
  robustness.
- `Temporal`, `recurrent` or a full syndrome history in a neural input did not by itself establish a
  physical memory model or the causal value of memory access.

## Stop judgment

The targeted search reached saturation for the four frozen rows when additional hits repeated one
of four already reviewed patterns: generic history-consuming neural decoders; static
noise/calibration conditioning; within-family rate or distance generalization; or synthetic
carrier-specific side information. No newly found full source simultaneously supplied the missing
object and the required matched/held-out evaluation.

This is a bounded coverage conclusion as of 2026-08-05, not a proof that no qualifying paper
exists. The safe reader-facing claims are the row decisions above, with the exact qualification
`in the reviewed evidence` wherever absence is material.
