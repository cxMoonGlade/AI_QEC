# Literature closure — coherent leakage reachability and long-range/loopy truncation (2026-07-13)

> **Workflow:** `theory-fix -> close-literature -> AnySearch academic search/citation chain ->
> deep-read-paper`. Local RAG/KG results are discovery only; every load-bearing statement below is
> tied to a full-text paper or explicitly marked `[ours]`. This packet audits literature and claim
> boundaries; it does not authorize experiment-code changes.

## Frozen claims

### C1 — coherent leakage tail

`Decision/consequence:` ADR 0011 Decision 3 would drop computational↔leakage coherence from the
scalable carrier. `Mechanism:` a coherent qutrit leakage channel, currently replaced by
computational/leakage pinching after each quarter-CZ slice while matching `L1,L2` populations.
`Observable:` the full multi-round joint binary `(detectors, obs)` law and a fixed-decoder LER.
`Bridge under audit:` matching `L1,L2` plus measurement-induced dephasing makes the coherent and
pinched channels record-equivalent. `Possible no-go:` schedule-dependent interference, channel
composition, and measurement placement can retain or erase the coherence differently.

### C2 — long-range/loopy PEPS truncation

`Decision/consequence:` bound the full-`d×d` single-wire PEPS carrier by removing long-range/loop
directions. `Mechanism:` WTG, FET, EAT, or ZMT finite-bond truncation using a local/full environment.
`Observable:` again the complete multi-round `(detectors, obs)` law and fixed-decoder LER, not bond
dimension or state overlap alone. `Bridge under audit:` a small WTG/ZMT/FET state/environment error
means the discarded directions are internal loop redundancy and therefore record-null.
`Possible no-go:` physical long-range correlations and virtual loop redundancy are distinct; a local
state objective need not control a rare global logical event.

## Executive correction

The literature does **not** support either active strong premise.

1. **Coherence reachability is channel- and schedule-dependent.** Varbanov et al. find a specific
   Surface-17 coherence-null regime; Marshall–Kafri find systematic exact-vs-STA differences in a
   different d3 coherent-leakage model; Manabe et al. show that an `L1,L2`-matched GTA can overestimate
   repetition-code LER by more than threefold. No source licenses per-quarter state pinching as a
   universal equivalent channel.
2. **WTG is not the general loopy solver.** Evenbly explicitly says WTG coefficients need not be
   physical and top-WTG truncation is optimal only at zero cycle entropy (near-optimal only when it is
   sufficiently small). At nonzero cycle entropy that direct optimality is lost and Evenbly proposes
   iterative FET; this is not a uniqueness theorem. Sokolov's ZMT improves
   initialization and removes exact zero modes, but every example retains variational refinement.
3. **No reviewed source closes the record bridge.** State norm, local/environment fidelity, cycle
   entropy, and bond saturation are internal diagnostics. A record/LER claim requires either a global
   trace/strategy-norm bound on the complete cq record object or a direct exact d3 record comparison.
4. **Large-`d` logical-coherence suppression is a different observable.** Behrends–Béri report
   numerical plus phenomenological exponential suppression of a syndrome-conditioned logical
   coherence for an independent X-only product channel. Their result contains no leakage, noisy
   repeated extraction, physical 2D PEPS, or truncation-to-record bridge, so it does not change the C1
   or C2 gate.

## Coverage ledger — C1 coherent leakage

| load-bearing row | required object | local evidence queried | external search queried | source / note | source location | status | implication |
|---|---|---|---|---|---|---|---|
| physical mechanism | coherent transfer between computational and leakage sectors | RAG `computational leakage coherence syndrome record stabilizer measurement`; KG concepts | `coherent leakage`, `qubit-leakage coherence`, `\|11⟩ ↔ \|02⟩`, transition/conditional phase | Wood–Gambetta 2018; Marshall–Kafri 2025; Varbanov 2020 | Wood definitions; Marshall Secs. II.D/III; Varbanov App. B Eqs. B7–B9 | closed | `L1,L2` do not specify cross-sector coherence; exchange coherence and leaked-neighbour conditional phase are distinct |
| principled incoherent surrogate | channel-level operation, not arbitrary state edit | Wood/Manabe notes | `subspace twirling approximation`, `generalized twirling approximation`, `dephasing`, `pinching` | [Marshall note](../papers/reading_notes/marshall_kafri_incoherent_leakage_sta_2312.10277.md); [Manabe note](../papers/reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md) | Marshall Eqs. 11–13; Manabe Eqs. 14–20 | closed | STA/GTA are source-defined channel constructions; per-slice project pinching is a different, stronger intervention |
| measurement-induced decay | schedule/instrument dependence | Varbanov and detector notes | `stabilizer measurement decoherence`, `phase irrelevant`, `ancilla measurement` | Marshall–Kafri; [Varbanov note](../papers/reading_notes/varbanov_leakage_detection_surface_2002.07119.md) | Marshall Eqs. 15–17; Varbanov App. B pp. 13–14 | closed within assumptions | repeated measurement can suppress coherence exponentially; Varbanov's schedule removes it operationally for the tested Z-basis case |
| contrary operational result | exact vs incoherent QEC output | existing Manabe note | `exact qutrit STA detector event logical error`, citation chain | Marshall Fig. 3; Manabe Fig. 8 | exact/STA d3 added LER; exact/GTA d19 repetition LER | closed | incoherent approximation can change detector marginals and LER even when leakage/seepage rates match |
| full-record observable | joint multi-round `(detectors,obs)` law | `docs/METRICS.md`; RAG result had DEF/pair/LER papers | `full syndrome record TV KL NLL`, `joint detector distribution` | no direct coherent-leakage paper found | Marshall reports DEF/LER; Manabe LER; Varbanov projection signatures/LER | missing | no paper validates the project's full joint-record equivalence |
| exact project intervention | four quarter-CZ slices, pinching after each, frozen XZZX instrument | `outputs/nonpauli_teacher/leakage_record_null.py/json` | exact phrase/synonym search plus backward/forward citation search | no matching published source found | N/A | missing | do not call the local operation “STA” or its result literature-closed |

## Coverage ledger — C2 long-range/loopy truncation

| load-bearing row | required object | local evidence queried | external search queried | source / note | source location | status | implication |
|---|---|---|---|---|---|---|---|
| internal loop correlation | distinguish virtual redundancy from physical correlation | RAG `finite bond PEPS truncation full syndrome record logical error rate long range correlation`; KG concepts | `closed loop TN canonical gauge`, `cycle entropy`, `long-range PEPS truncation` | [Evenbly note](../papers/reading_notes/evenbly_gauge_closed_loops_1801.05390.md) | Sec. IV, Eq. 11, PDF p. 5 | closed | WTG spectrum alone is not a physical-state spectrum on cyclic networks |
| WTG direct truncation boundary | when canonical coefficients may be cut | existing Mc Keever/Sokolov notes | Evenbly citation chain | Evenbly 2018 | Sec. IV, PDF p. 5 | closed | top-WTG is optimal at `S_cycle=0`, only near-optimal heuristically when small; not general for loopy bonds |
| FET objective/solver | nonzero-cycle truncation | Mc Keever note | `full environment truncation global optimum`, failure/initialization terms | Evenbly 2018; Mc Keever–Szymańska 2021 | Evenbly Sec. V Eq. 12; Mc Keever Eq. 9/appendices | closed | FET alternates generalized eigen/SVD updates; “global optimum” is empirical suggestion, not theorem; approximate environment limits the objective |
| exact zero-mode removal | lossless removal of a linear dependence | Sokolov note | `zero mode gauge truncation` | [Sokolov note](../papers/reading_notes/sokolov_dziarmaga_zeromode_gauge_truncation_2508.00338.md) | Eqs. 1–5, 11–19 | closed | `f=0` is lossless; small positive `f` is not a physical-vs-redundant classifier; ZMT is initialization |
| global state certificate | norm covering whole simulated object | Werner note | `tensor network global trace norm truncation bound` | [Werner note](../papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md) | Theorem 7 | closed only for 1D local Markov LPTN | a true global cq-state trace bound would control record TV, but Werner's assumptions do not cover this PEPS/FET trajectory |
| full-record / rare-LER bridge | `TV(P_record,Q_record)` and fixed-decoder event | `docs/METRICS.md`; QEC TN notes | 41 exact AnySearch queries plus DOI citation chains; see Search-exhaustion record | no direct theorem found; BSV/Piveteau/Manabe are empirical convergence examples | N/A | confirmed-literature-gap | local fidelity or bond convergence cannot be promoted to record/LER fidelity; rare relative error needs global error `epsilon << p_L` |
| long-range measurement memory | instrument-specific temporal range | process-tensor RAG/KG | `quantum Markov order instrument specific`, local-observable Lieb–Robinson | Taranto et al. 2019; Barthel–Kliesch 2012 | theorem scopes | closed as no-go boundary | local-observable/quasilocal bounds do not automatically cover a growing full record or global logical string |

## Metric adjudication

Published QEC experiments/model papers most commonly compare detector marginals, `p_ij`/correlation
matrices, and frozen-decoder logical error. Full-distribution TV/JSD appears in nearby noise-learning
work, and classifier BCE/NLL appears in learned decoding, but this search found no peer-reviewed QEC
simulator standard that mandates **full multi-round record** TV/KL/NLL.

Therefore:

- TV and KL remain mathematically standard distribution distances and are appropriate **project
  certification metrics** at exact d3; they should not be described as already universal QEC practice.
- held-out record NLL is appropriate only for a normalized generative model of `P(record)`; decoder
  classifier BCE estimates `P(logical | record)` and is not the same object.
- the local diagnostic's aggregate two-proportion `T` over detector marginals and within-round pairs is
  project-defined and incomplete. It may detect a difference, but it is neither full-record TV/KL nor
  a sufficient statistic theorem for the current channels.

### Correct trace-distance bridge [ours, standard data processing]

Let `rho_RS` and `rho_tilde_RS` retain the complete classical record register `R`. If

```text
D(rho_RS,rho_tilde_RS) = 1/2 ||rho_RS-rho_tilde_RS||_1 <= epsilon,
```

then `TV(P_R,P_tilde_R) <= epsilon`. For a fixed decoder/failure event,
`|p_L-p_tilde_L| <= epsilon`; the relative-error bound is only `epsilon/p_L`. A rare LER therefore
requires `epsilon << p_L`. A bound on the final reduced system state after discarding `R` cannot be
inverted into a historical-record bound.

## Audit of the current local “definitive” experiment [ours]

`outputs/nonpauli_teacher/leakage_record_null_wc.json` is useful local evidence that the two implemented
channels produce distinguishable sampled statistics, but its `definitive=true` label exceeds both the
implementation and literature support:

- the carrier is a **nine-data-qutrit** state-vector trajectory. It includes parsed single-qutrit gate
  layers and per-CZ leakage slices, but the syndrome instrument is compiled into a data-side stabilizer
  POVM; it does not explicitly evolve transmon ancillas through the physical CZ/measurement dynamics
  used in Marshall or Varbanov;
- Arm B applies `deph2 o E_slice` after each slice. This is not Marshall's channel-level STA and has no
  published equivalence theorem for the frozen XZZX schedule;
- the gate statistic is a custom Gaussian/chi-square surrogate on detector marginals and within-round
  pairs. It is not the full joint-record TV/KL/NLL and no sufficiency result is supplied;
- `L1,L2` are matched per slice, which Manabe directly shows is not enough to fix logical behavior in
  another QEC setting.

The result should be classified as a **project diagnostic / hypothesis generator**. It can falsify
equality for the two implemented channels, but cannot establish that the observed magnitude is a
faithful physical effect or that the carrier must preserve the same tail on real hardware.

## Anomaly ledger

| contrary fact / ambiguity | source and exact location | affected object | implication | status/action |
|---|---|---|---|---|
| exact coherent vs STA differs and exact depends on anharmonicity | Marshall Fig. 3; App. E Fig. 12 | C1 record/LER bridge | coherence can survive into QEC observables | ADR universal null contradicted; exact project arm remains open |
| setting `rho_coh=0` has no effect in tested Surface-17 Z-basis case | Varbanov App. B pp. 13–14 | C1 universal reachability | coherence is not universally required | retain schedule-specific null arm |
| same `L1,L2`, >3x LER overestimate | Manabe Eqs. 14–20, Fig. 8 | rate-matching premise | population rates are insufficient channel descriptors | add exact-vs-GTA reproduction control |
| WTG coefficients differ for representations of the same state | Evenbly Sec. IV, Fig. 4 | C2 physical classifier | WTG spectrum cannot label genuine long-range physics | handoff WTG-primary claim contradicted |
| at `S_cycle != 0`, top-WTG optimality is lost and the paper proposes iterative FET | Evenbly Sec. V, PDF p. 6 | C2 deterministic replacement | WTG alone is not licensed as a global solver; FET is the source's proposal, not a unique-solver theorem | reopen solver design |
| ZMT always followed by variational optimization | Sokolov examples, Secs. VI–X | C2 solver claim | ZMT is initialization, not global solver | retain/refactor refinement step; do not overclaim |
| environment/state fidelity has no full-record theorem | Evenbly/Mc Keever vs Werner theorem scope | C2 record bridge | internal metric cannot license record/LER | require d3 record oracle or global cq bound |
| X-only logical coherence decreases with `d`, but the paper has no leakage/record/PEPS object | [Behrends–Béri note](../papers/reading_notes/surface_code_beyond_pauli_2412.21055.md), Fig. 1(d), Secs. VI/VII.D | C1/C2 large-`d` shortcut | logical-channel scaling cannot be substituted for physical-tail or truncation error | retain as published adjacent evidence; gate unchanged |

## External acquisition ledger

The acquisition below distinguishes a source that directly proves the target bridge from a source
that only supplies one side of it.  For C2, the target bridge is:

> a local WTG/FET/simple-update/ZMT truncation quantity quantitatively controls the law of the full
> multi-round QEC `(detectors, obs)` record in TV/KL/NLL, or the rare fixed-decoder logical-error
> probability derived from that record.

The direct-source count for that statement is **0**, not two or more.  The closest sources and the
reason each one is not a direct bridge are:

| candidate | publication and source | verified load-bearing content | direct-bridge disposition |
|---|---|---|---|
| Evenbly, *Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops* | PRB 98, 085155 (2018), [DOI](https://doi.org/10.1103/PhysRevB.98.085155); local full read `evenbly_gauge_closed_loops_1801.05390.md` | Eq. 12 optimizes pure-state overlap in the full environment; Secs. IV–V show that WTG coefficients are representation-dependent and top-WTG truncation loses its optimality when cycle entropy is nonzero | **reject as direct bridge:** no cq record, strategy norm, TV/KL/NLL, or QEC logical-event theorem |
| Mc Keever–Szymańska, *Dynamics of two-dimensional open quantum lattice models with tensor networks* | PRX 11, 021035 (2021), [DOI](https://doi.org/10.1103/PhysRevX.11.021035); local full read `mc_keever_stable_ipepo_fet_wtg_2012.12233.md` | FET uses a normalized Hilbert–Schmidt objective with an approximate CTMRG environment and benchmarks local reduced-state trace distance; in the weak-dissipation/long-correlation regime, finite-`D` curves visibly depart at later time | **reject; adverse limitation:** an internal/local diagnostic is not a complete-record certificate, and the long-correlation example shows that a locally stable procedure need not remain accurate in the hard regime |
| Werner et al., *Positive tensor network approach for simulating open quantum many-body systems* | PRL 116, 237201 (2016), [DOI](https://doi.org/10.1103/PhysRevLett.116.237201); Theorem 7 / Eq. 60, PDF p. 11 visually checked | proves a global trace-norm error bound for a 1D nearest-neighbour Markovian Liouvillian evolved with locally purified tensor networks | **partial formal bridge only:** a global trace bound could control a retained cq record by data processing, but the theorem does not cover a 2D PEPS/FET/WTG trajectory, adaptive multi-round instrument, or a record that has already been discarded |
| Gutoski–Rosmanis–Sikora, *Fidelity of quantum strategies with applications to cryptography* | Quantum 2, 89 (2018), [DOI](https://doi.org/10.22331/q-2018-09-03-89), arXiv:1704.04033v2; Eqs. 7 and 10, PDF pp. 3–4 visually checked | defines the strategy norm by maximization over compatible co-strategies and relates it to strategy fidelity | **partial formal bridge only:** this is the correct multi-round operational distance, but no result maps a local FET/WTG score to that norm |
| Bravyi–Suchara–Vargo, *Efficient algorithms for maximum likelihood decoding in the surface code* | PRA 90, 032326 (2014), [DOI](https://doi.org/10.1103/PhysRevA.90.032326); PDF pp. 15–16 visually checked | MPS bond truncation approximates logical-coset probabilities for perfect syndrome extraction; the paper says precision has no direct estimator in the depolarizing case and observes poorer convergence for unlikely cosets | **reject; adverse limitation:** empirical decoder convergence is not an error theorem, and the least-likely cosets are exactly where a rare-event claim can be fragile |
| Piveteau–Chubb–Renes, *Tensor Network Decoding Beyond 2D* | PRX Quantum 5, 040303 (2024), [DOI](https://doi.org/10.1103/PRXQuantum.5.040303); local full text and reading note | uses approximate 3D contraction by sweeping a 2D PEPS/simple-update boundary to calculate logical-coset posteriors for repeated noisy-syndrome QEC; reports LER versus bond dimension and notes numerical degradation and the lack of a PEPS canonical form | **closest published QEC candidate, but reject as direct bridge:** it supplies empirical LER convergence, not the full record law or a local-truncation-score-to-LER bound |
| Manabe–Suzuki–Darmawan, *Efficient simulation of leakage errors in quantum error-correcting codes using tensor network methods* | NJP (2025), [DOI](https://doi.org/10.1088/1367-2630/ae1529); local full text and reading note | controls MPS truncation with discarded singular-value 2-norm thresholds and checks that chosen thresholds are sufficient in the studied LER parameter range | **reject as direct bridge:** empirical, quasi-1D canonical-MPS convergence is not a 2D PEPS/FET full-record or rare-LER guarantee |
| Rudolph–Tindall, *Simulating and Sampling from Quantum Circuits with 2D Tensor Networks* | arXiv:2507.11424v2, [preprint](https://arxiv.org/abs/2507.11424); local full text and reading note | compares terminal pure-state PEPS samples using a separately evaluated sample KL divergence; the product of local retained weights is presented as an empirically useful fidelity proxy | **reject as direct bridge:** no mid-circuit record, mixed PEPO, QEC logical event, or theorem deriving the reported KL from the local proxy; the acquisition route returned a preprint, not a peer-reviewed direct source |
| Sason, *f-Divergence Inequalities* / reverse-Pinsker results | IEEE TIT 62 (2016), [DOI](https://doi.org/10.1109/TIT.2016.2603151); precursor arXiv:1503.07118 | KL upper bounds from TV require support or bounded-likelihood-ratio / probability-floor conditions | **metric limitation, not a bridge:** even a TV certificate cannot silently be promoted to an NLL/KL certificate without the extra assumptions |

The earlier C1 acquisition remains unchanged in substance: Marshall–Kafri
([DOI](https://doi.org/10.1103/PhysRevApplied.23.054025)), Manabe–Suzuki–Darmawan,
and Varbanov et al. ([DOI](https://doi.org/10.1038/s41534-020-00330-w)) close adjacent
coherent-leakage rows, but no source was found for the exact project-specific quarter-slice XZZX
intervention.

## Search-exhaustion record

### Local retrieval first

The repo RAG was queried with the following exact strings (`--top-k 12`):

```text
PEPS FET WTG truncation full syndrome record total variation KL NLL logical error rate
tensor network approximation error bound measurement outcome distribution rare event probability quantum error correction
finite bond PEPS local environment fidelity global trace distance process tensor record distribution
tensor network decoder truncation convergence rare logical error rate surface code
```

It returned the Evenbly, Mc Keever, Werner, Bravyi–Suchara–Vargo, Piveteau,
Manabe, Rudolph–Tindall, and process/strategy-distance clusters summarized above; none contained the
target implication.  The local KG (`354` nodes, `262` papers, `53` concepts at query time) was checked
with `stats`, `topics`, `concept "tensor network truncation"`, `concept "syndrome record"`,
`concept "trace distance"`, `concept "logical error rate"`, `concept "FET"`, `concept "WTG"`,
the relevant `paper` queries, and the `concept_trace_distance` neighbours.  It had no exact concept
node for tensor-network truncation, syndrome record, logical error rate, FET, or WTG; the 31-paper
trace-distance cluster supplied only adjacent metric results.  RAG/KG hits were treated as discovery,
not as evidence; the load-bearing candidates in the table were checked against full text.

### AnySearch academic acquisition

`get_sub_domains --domain academic` was run first.  Search then used `academic.search`,
`academic.preprint`, and forward/backward `academic.citation` routes on 2026-07-13.  These are the
exact direct-bridge queries that were run:

```text
PEPS truncation error syndrome record total variation quantum error correction
full environment truncation logical error rate quantum error correction
tensor network approximation KL divergence syndrome distribution
bond dimension convergence logical error rate surface code tensor network
tensor network truncation bound decoder failure probability
tensor network decoder bond dimension convergence logical error probability
boundary MPS truncation error surface code decoding accuracy
PEPS simulation syndrome distribution truncation error
tensor network maximum likelihood decoder approximation error guarantee
rare logical error tensor network simulation truncation
PEPS FET WTG truncation "syndrome history" logical failure
tensor network truncation "detection events" surface code record distribution
PEPS approximation "logical error rate" bond dimension syndrome measurements
"full environment truncation" "logical error"
FET WTG syndrome record total variation
```

The general theorem, metric, and no-go queries were:

```text
trace norm tensor network truncation measurement outcome distribution bound
local fidelity global trace distance PEPS truncation counterexample
rare event probability error bound tensor network contraction
process tensor approximation diamond norm multi-time measurement statistics
quantum comb strategy norm tensor network truncation error
matrix product state truncation error total variation measurement outcomes
TEBD discarded weight bound global wavefunction norm measurement probability distribution
PEPS truncation rigorous global error bound local fidelity
approximate quantum state fidelity total variation sampling distribution tensor network
certified tensor network sampling total variation distance bond truncation
process tensor approximation operational distance multi-time measurement statistics
quantum comb strategy norm distinguishability measurement outcome distributions
trace distance total variation measurement data processing quantum states
relative entropy upper bound total variation minimum probability
rare event relative error total variation probability bound
"On Reverse Pinsker Inequalities"
"upper bound" relative entropy total variation minimum probability reverse Pinsker
"Measuring the distance of quantum processes" quantum comb
"strategy norm" quantum strategies distinguishability
"process tensor" "operational distinguishability"
```

One route for `approximate quantum state fidelity total variation sampling distribution tensor
network` was transiently unavailable; the neighbouring fidelity/TV, certified-sampling, trace-norm,
and exact-title variants succeeded, so it was not counted as evidence or as an unresolved backend
outage.  Exact-title acquisition was also run for:

```text
"Efficient algorithms for maximum likelihood decoding in the surface code"
"Linear-time general decoder for the surface code"
"Tensor Network Decoding Beyond 2D"
"Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes Using Tensor Network Methods"
Rudolph Tindall GPU PEPS quantum circuit sampling total variation fidelity
"Fidelity of quantum strategies with applications to cryptography"
```

Forward and backward citation walks were run by exact DOI for Evenbly
(`10.1103/PhysRevB.98.085155`), Mc Keever (`10.1103/PhysRevX.11.021035`), Werner
(`10.1103/PhysRevLett.116.237201`), Bravyi–Suchara–Vargo
(`10.1103/PhysRevA.90.032326`), and Piveteau (`10.1103/PRXQuantum.5.040303`).  The title-only WTG
route was polluted by the unrelated wind-turbine acronym, so only exact-title/DOI hits were retained.
The chains added applications and algorithmic variants but no source with the target implication.

Terminology coverage included PEPS/PEPO/boundary-MPS/MPS, FET/full-environment truncation,
WTG/weighted-trace gauge, simple update, discarded weight, bond dimension, syndrome/detection-event/
history/full record, measurement instrument/quantum comb/process tensor/strategy norm, TV/trace norm/
KL/NLL, decoder failure/logical coset/logical error/rare event, and convergence/certificate/error bound.

### Exhaustion judgement for C2

No searched published source both (a) starts from a local PEPS truncation diagnostic and (b) derives
a quantitative full-record or rare-LER guarantee.  The two halves exist separately: Werner and
Gutoski et al. provide appropriate global operational distances under different hypotheses, while
Bravyi–Suchara–Vargo, Piveteau et al., and Manabe et al. provide empirical QEC convergence checks.
Composing those papers into the desired theorem would be a new project derivation, not a cited result.

Therefore the **specific C2 mechanism-to-record bridge row** is promoted from `missing` to
`confirmed-literature-gap` under the skill's search-status meaning.  This records that the above local,
external, synonym, exact-title, and citation-chain search found no direct bridge; it is **not** a
mathematical proof that no such paper exists and must be reopened if a new candidate is found.  The C1
exact quarter-slice intervention was not exhaustively re-searched in this pass and remains
`missing/open`.

## Closure verdict

- `closure_status: open`
- `C2_local_truncation_to_full_record_or_rare_LER: confirmed-literature-gap`
- **Answer to the direct-support gate:** there are **zero** papers directly supporting the complete
  C2 implication, so the required `>=2` independent direct sources is not met.  Evenbly plus Mc Keever
  support FET/WTG method boundaries; Werner plus Gutoski support global-distance/strategy-norm
  machinery; Piveteau plus Bravyi–Suchara–Vargo plus Manabe support empirical QEC convergence.  None
  proves the bridge between those layers.
- **Contradicted premises:** universal coherent-tail record-null; `L1,L2` sufficiency; deterministic
  top-WTG global-optimum replacement; small positive ZMT/FET error as physical-redundancy classifier.
- **Closed rows:** STA/GTA definitions; schedule-specific measurement dephasing; published exact-vs-
  incoherent counterexamples; WTG/cycle/FET/ZMT algorithm boundaries; the conditional trace-distance
  data-processing bridge.
- **Remaining gaps:** exact quarter-slice XZZX full-record comparison; explicit data+ancilla physical
  instrument; a project derivation or independent oracle for global cq/strategy error under finite
  PEPS truncation; rare-LER accuracy `epsilon << p_L`.  The last condition follows because an absolute
  event-probability error `epsilon` only gives relative LER error of order `epsilon / p_L`; it is a
  project-side composition, not a theorem supplied by a target paper.
- **Load-bearing notes:** Marshall–Kafri, Evenbly, Mc Keever, Werner,
  Bravyi–Suchara–Vargo, Piveteau, Manabe, Varbanov, Sokolov, Rudolph–Tindall; Gutoski et al. was
  checked from the published PDF for the strategy-norm equations.
- **Supported implementation path:** none yet. A paper-faithful reproduction/prereg may compare
  (i) Varbanov-like schedule null, (ii) Marshall exact-vs-STA non-null, and (iii) the project-specific
  per-slice ablation, all on the same full record metric and explicit ancilla instrument.  For C2,
  preregister either an exact-`d=3` full-record comparison or a derivation that retains the cq record
  and proves a global trace/strategy bound; do not use the local truncation score itself as the record
  certificate.
- **Allowed downstream action:** correct documentation and design that reproduction/preregistration.
  **STOP** claim propagation, new truncation implementation, and “definitive” scientific labeling until
  the missing bridge is independently closed.
