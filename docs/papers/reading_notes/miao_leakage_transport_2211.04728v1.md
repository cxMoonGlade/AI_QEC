+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2211.04728"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2211.04728v1"
source_artifact = "docs/papers/miao_overcoming_leakage_scalable_2211.04728.pdf"
source_sha256 = "f82e81b7f62dd1ac5d14e27c4d4b6c0b0a81f5aae9e96b1f45973a48d8991e40"
title = "Overcoming leakage in scalable quantum error correction"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/MIAO_2211_04728_CLAIM_AUDIT_2026-07-15.md"
audit_packet_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
admission_status = "draft_pending_review"
admission_reviewer = "pending_dual_review"
admission_date = "2026-07-15"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16]

[[relations]]
predicate = "uses"
object_id = "diabatic-cz-gate"
object_type = "method"
object_label = "diabatic CZ gate"
fact_id = "fact.cz-resonances"

[[relations]]
predicate = "defines"
object_id = "leakage-transport-processes"
object_type = "concept"
object_label = "leakage transport processes"
fact_id = "fact.cz-resonances"

[[relations]]
predicate = "derives"
object_id = "effective-coupling"
object_type = "model"
object_label = "effective coupling"
fact_id = "fact.effective-coupling"

[[relations]]
predicate = "defines"
object_id = "relative-population-transport"
object_type = "observable"
object_label = "relative population transport"
fact_id = "fact.relative-population-observable"

[[relations]]
predicate = "measures"
object_id = "leakage-phase-shift"
object_type = "observable"
object_label = "leakage-state phase shift"
fact_id = "fact.leakage-phase"

[[relations]]
predicate = "measures"
object_id = "cycle-leakage-population"
object_type = "observable"
object_label = "leakage population in each cycle"
fact_id = "fact.cycle-population-scale"

[[relations]]
predicate = "defines"
object_id = "autocorrelation-matrix"
object_type = "observable"
object_label = "autocorrelation matrix"
fact_id = "fact.autocorrelation-definition"

[[relations]]
predicate = "limits"
object_id = "within-cycle-leakage-dynamics"
object_type = "limitation"
object_label = "leakage dynamics inside a single cycle"
fact_id = "fact.within-cycle-limitation"
+++
# Full-text review — Miao et al., "Overcoming leakage in scalable quantum error correction"

## Source identity [paper_fact]
Fact ID: fact.source-identity
Source locator: PDF p. 1, title, author, arXiv-version, and date block
PDF page: 1
Claim: The arXiv v1 manuscript is titled "Overcoming leakage in scalable quantum error correction," lists Kevin C. Miao and Matt McEwen as equal-contribution first authors, and is dated November 10, 2022.

The later journal version uses the shorter title "Overcoming leakage in quantum error correction."

## Selection scope [paper_fact]
Fact ID: fact.selection-scope
Source locator: Abstract and final paragraph of the introduction, PDF pp. 1--2
PDF page: 1
Claim: The manuscript studies the spread, removal, and logical effects of transmon leakage in distance-3 surface-code and distance-21 bit-flip-code experiments on a Sycamore processor.

The experiments compare no reset, measure-qubit leakage removal, and data-qubit leakage removal.

## Injected-leakage decay and spread [paper_fact]
Fact ID: fact.injected-decay-spread
Source locator: Sec. 1, Fig. 1c and accompanying paragraph
PDF page: 2
Claim: Injected `|2>` population on the central data qubit decayed with an exponential constant around 4.4 surface-code cycles while excess leakage population also appeared on neighboring qubits.

Each cycle took approximately one microsecond, and the population was measured at the end of each
cycle.

## Diabatic-CZ resonances [paper_fact]
Fact ID: fact.cz-resonances
Source locator: Sec. 1, Fig. 2a and accompanying paragraphs
PDF page: 3
Claim: In the studied diabatic CZ gate, a calibrated `2 pi` rotation on `|11> <-> |20>` also aligns a mediated `|30> <-> |12>` resonance and a direct `|31> <-> |22>` resonance, which the source calls leakage transport processes.

Two-qubit states are ordered with the higher-energy qubit first.

## Gate dependence of transport [paper_fact]
Fact ID: fact.transport-gate-dependence
Source locator: Sec. 1, paragraph preceding Fig. 2b
PDF page: 3
Claim: The amount of leakage transport was not normally calibrated and depended on the chosen gate length and effective coupling between levels.

The statement is scoped to the diabatic CZ gates examined in the manuscript.

## Relative-population observable [paper_fact]
Fact ID: fact.relative-population-observable
Source locator: Sec. 1, Fig. 2b--c and caption
PDF page: 3
Claim: The relative population transport `Delta P_t` is the net change in state population obtained by subtracting a baseline experiment without a CZ gate from the corresponding experiment with a CZ gate.

The displayed matrix includes the first two leakage levels.

## Headline transport magnitudes [paper_fact]
Fact ID: fact.transport-magnitudes
Source locator: Sec. 1, Fig. 2b and accompanying paragraph
PDF page: 3
Claim: The reported average absolute relative population transport was around `18%` for `|30> <-> |12>` and around `61%` for `|31> <-> |22>` on the measured device.

The figure also shows indications of higher resonances such as `|42> <-> |33>`.

## Leakage-state phase shift [paper_fact]
Fact ID: fact.leakage-phase
Source locator: Sec. 1, Fig. 2d--e and accompanying paragraph
PDF page: 3
Claim: A modified Ramsey experiment over 20 qubit pairs measured a leakage-state phase shift near `0.65 pi` on the lower-energy qubit when the higher-energy neighbor was prepared in `|2>` during a CZ gate.

The corresponding computational-state preparations grouped near zero and `pi`.

## Printed ladder couplings [paper_fact]
Fact ID: fact.printed-ladder-couplings
Source locator: Supplementary Sec. S1, displayed coupling equations
PDF page: 10
Claim: After defining `g` as the induced `|11> <-> |20>` coupling, the source prints `g_30,21 = sqrt(3) g` and `g_21,12 = 2 g` for the mediated higher-level path.

This record preserves both the prose definition and the displayed factors exactly as printed.

## Printed effective coupling [paper_fact]
Fact ID: fact.effective-coupling
Source locator: Supplementary Sec. S1, displayed effective-coupling equation
PDF page: 10
Claim: The printed effective coupling for `|30> <-> |12>` is `g_eff = -(g_21,12 g_30,21)/eta`, where `|21>` is the virtual intermediate level detuned by the nonlinearity `eta`.

The expression is presented as a second-order estimate for the two-photon transition.

## Population-transport estimate [paper_fact]
Fact ID: fact.transport-estimate
Source locator: Supplementary Sec. S1, displayed population-transport equation
PDF page: 10
Claim: For a gate maintaining the coupling for time `t`, the source estimates population transport as `P_t = sin^2(g_eff t)`.

The estimate immediately follows the printed effective-coupling expression.

## Readout and baseline construction [paper_fact]
Fact ID: fact.readout-baseline
Source locator: Supplementary Sec. S1, Fig. S1a--b and accompanying paragraphs
PDF page: 10
Claim: The transport experiment used simultaneous readout resolving levels zero through three, assigned level four as level three, and formed the displayed transport matrix by subtracting the baseline matrix from the with-CZ matrix.

The baseline consisted of state preparation followed directly by simultaneous readout.

## Directional transport for the mediated resonance [paper_fact]
Fact ID: fact.directional-transport-30-12
Source locator: Supplementary Sec. S1, Fig. S1c
PDF page: 11
Claim: For `|30> <-> |12>`, Fig. S1c reports signed relative-population changes of `-19%`, `17%`, `19%`, and `-18%` across the two input and two output states.

The signs record net population loss or gain after baseline subtraction.

## Directional transport for the direct resonance [paper_fact]
Fact ID: fact.directional-transport-31-22
Source locator: Supplementary Sec. S1, Fig. S1c
PDF page: 11
Claim: For `|31> <-> |22>`, Fig. S1c reports signed relative-population changes of `-65%`, `58%`, `61%`, and `-60%` across the two input and two output states.

The signs record net population loss or gain after baseline subtraction.

## Transport aggregation rule [paper_fact]
Fact ID: fact.transport-aggregation
Source locator: Supplementary Sec. S1, Fig. S1c caption and following paragraph
PDF page: 11
Claim: The headline transport value for each resonance is the mean of the absolute values of its signed relative-population changes.

This aggregation produces the values printed below Fig. 2b.

## Cycle population scale [paper_fact]
Fact ID: fact.cycle-population-scale
Source locator: Sec. 2, Fig. 3c and accompanying paragraph
PDF page: 5
Claim: Moment-resolved measurements estimated that circuit operations produced around `5 x 10^-3` leakage population in each cycle, with data qubits under data-qubit leakage removal rising from around `1 x 10^-3` at cycle start to around `5 x 10^-3` immediately after measurement before reset.

The values are average populations at specified moments of the reported QEC protocol.

## Within-cycle limitation [paper_fact]
Fact ID: fact.within-cycle-limitation
Source locator: Sec. 3, paragraph preceding Fig. 5
PDF page: 6
Claim: The numerical simulations slightly underestimated the logical error induced by injected leakage, and the source identifies leakage dynamics inside a single cycle as requiring future work.

This limitation remained even when removal prevented substantial leakage spread across cycles.

## Hypothetical simulation model [paper_fact]
Fact ID: fact.hypothetical-model-scope
Source locator: Supplementary Sec. S6 and Table S1
PDF page: 15
Claim: The distance-5 and distance-7 scaling study used a hypothetical device error model with no baseline leakage source at zero injected leakage and injected leakage varied under two removal strategies.

The simulations used Kraus operators for transport, phase errors, and removal parameters.

## Hypothetical timing and coherence values [paper_fact]
Fact ID: fact.hypothetical-model-values
Source locator: Supplementary Sec. S6, Table S1
PDF page: 15
Claim: The hypothetical model lists a `25 ns` CZ-gate time and qubit `T1 = 75 us` and `T2 = 75 us`.

The same table lists a `15 ns` single-qubit-gate time and a `300 ns` combined readout-and-reset time.

## Autocorrelation definition [paper_fact]
Fact ID: fact.autocorrelation-definition
Source locator: Supplementary Sec. S7, Eq. (S6)
PDF page: 15
Claim: The autocorrelation matrix `pbar_t,t'` averages detection-graph edge probabilities `p_ij` over node pairs on the same stabilizer for arbitrary time separation.

Under the stated independent-Pauli idealization, elements at separations greater than one cycle are
expected to vanish.

## DQLR non-local correlations [paper_fact]
Fact ID: fact.dqlr-correlations
Source locator: Supplementary Sec. S7, Fig. S7a--b and accompanying paragraphs
PDF page: 16
Claim: With data-qubit leakage removal, measured same-stabilizer non-local correlation magnitudes exceeded `2 x 10^-3` only at separation two and were otherwise below `0.2%` through separation ten, with variations below `1 x 10^-3` unresolved by the stated one-standard-deviation error bars.

No-reset and measure-qubit-removal data retained larger and longer-ranged correlations.

## Coupling-normalization gap [literature_gap]
Fact ID: gap.coupling-normalization
Source locator: Supplementary Sec. S1, displayed coupling equations
PDF page: 10
Claim: The source does not reconcile its definition of `g` as the induced `|11> <-> |20>` coupling with the printed `sqrt(3) g` and `2 g` higher-level factors.
Gap scope: source_local

The printed statements are retained without supplying an unstated normalization.

## Channel-rate-equivalence gap [literature_gap]
Fact ID: gap.channel-rate-equivalence
Source locator: Sec. 1, Fig. 2b--c; Sec. 2, Fig. 3c
PDF page: 3
Claim: The source does not equate its baseline-subtracted relative population transport or moment-resolved cycle population with a channel-averaged leakage rate.
Gap scope: source_local

The observables have different experimental definitions within the manuscript.

## Universal-transport-calibration gap [literature_gap]
Fact ID: gap.universal-transport-calibration
Source locator: Sec. 1, paragraph preceding Fig. 2b
PDF page: 3
Claim: The source does not establish the reported transport magnitudes as gate-independent or device-independent calibration values.
Gap scope: source_local

It states that transport depends on gate length and effective coupling.

## Pure-dephasing-time gap [literature_gap]
Fact ID: gap.pure-dephasing-time
Source locator: Supplementary Sec. S6, Table S1
PDF page: 15
Claim: The source lists `T2 = 75 us` but does not identify that value as a pure-dephasing time.
Gap scope: source_local

No separate pure-dephasing parameter is provided in the table.
