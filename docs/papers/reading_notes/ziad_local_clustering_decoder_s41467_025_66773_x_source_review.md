+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.1038/s41467-025-66773-x"
source_version = "version-of-record"
source_uri = "https://doi.org/10.1038/s41467-025-66773-x"
source_artifact = "outputs/overview/literature/coverage_validation/sources/Ziad_2025_NatCommun_local_clustering_decoder.pdf"
source_sha256 = "e245fe9a81ef635d9cda9421f416e27372aecb37b283d25d7951333a47428fa0"
title = "Local clustering decoder as a fast and adaptive hardware decoder for the surface code"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/ZIAD_LOCAL_CLUSTERING_DECODER_10_1038_S41467_025_66773_X_AUDIT_2026-08-05.md"
audit_packet_sha256 = "b1de4a36e3d662fe4408a1c7b2153372b162c6378813b6c12a29e3055a0ffed6"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_qadapt"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

[[relations]]
predicate = "defines"
object_id = "ziad-classical-leakage-register"
object_type = "model"
object_label = "classical leakage register"
fact_id = "ziad-leakage-register"

[[relations]]
predicate = "uses"
object_id = "ziad-patch-wiggling"
object_type = "method"
object_label = "patch wiggling"
fact_id = "ziad-patch-wiggling-horizon"

[[relations]]
predicate = "derives"
object_id = "ziad-leakage-herald-adaptation"
object_type = "method"
object_label = "leakage herald"
fact_id = "ziad-adaptivity-map"

[[relations]]
predicate = "uses"
object_id = "ziad-unweighted-lcd"
object_type = "method"
object_label = "unweighted Local Clustering Decoder"
fact_id = "ziad-decoder-computation"

[[relations]]
predicate = "supports"
object_id = "ziad-population-leakage-decoder-comparison"
object_type = "observable"
object_label = "adaptive and non-adaptive unweighted LCD"
fact_id = "ziad-population-comparison"

[[relations]]
predicate = "supports"
object_id = "ziad-fpga-decoding-time"
object_type = "observable"
object_label = "reported decoder-engine times"
fact_id = "ziad-fpga-timing"

[[relations]]
predicate = "limits"
object_id = "ziad-partner-depolarisation-boundary"
object_type = "limitation"
object_label = "maximal depolarisation"
fact_id = "ziad-partner-channel-boundary"

[[relations]]
predicate = "limits"
object_id = "ziad-reproducibility-boundary"
object_type = "limitation"
object_label = "RTL/implementation source"
fact_id = "ziad-artifact-boundary"
+++
# Full-text review — Ziad et al., "Local clustering decoder as a fast and adaptive hardware decoder for the surface code"

## Source identity [paper_fact]
Fact ID: ziad-source-identity
Source locator: Main article title page and publication history; publisher Supplementary Information title page; publisher peer-review-file title page
PDF page: 1
Claim: The fixed source is the version-of-record article published in *Nature Communications* 16, 11048 on 17 December 2025, together with its official three-page Supplementary Information and fourteen-page peer-review file.

The main artifact has DOI `10.1038/s41467-025-66773-x`. The associated Supplementary Information
and peer-review PDFs have SHA-256 values
`fde130c1e7418d800cd2ea462518de6dc3cea8a590251bf328e6f60c5f055b73` and
`0968fbd4684aa4d7b6e38071123da2c2935b00eb48e4dd857e8175eb470dcec6`, respectively.

## Selection scope [paper_fact]
Fact ID: ziad-selection-scope
Source locator: Abstract; Results, "LCD" and "Performance"; Methods, "Modelling leakage with Pauli Frame tracking"
PDF page: 1
Claim: The source implements an FPGA Local Clustering Decoder and evaluates leakage-herald-conditioned decoding of simulated repeated rotated-surface-code memory circuits.

The scientific demonstration joins a stochastic circuit-level leakage generator, a
measurement-derived herald interface, an unweighted graph decoder and FPGA execution characterized
by decoder-state-machine cycle counts and implementation clock frequencies.

## Classical leakage register [paper_fact]
Fact ID: ziad-leakage-register
Source locator: Methods, "Modelling leakage with Pauli Frame tracking," opening and numbered state-transition items, pp. 8--10
PDF page: 9
Claim: The modified Stim simulator assigns each qubit a classical leakage register that remains set after leakage until a sampled relaxation or reset returns the qubit to the sealed state.

The register is separate from the Pauli register. It is a stochastic classical representation of
out-of-subspace persistence, not a qutrit density-matrix trajectory.

## Patch-wiggling horizon [paper_fact]
Fact ID: ziad-patch-wiggling-horizon
Source locator: Main Results, "Decoding the surface code"; Supplementary Information, Appendix A.2
PDF page: 3
Claim: Patch wiggling alternates data and auxiliary roles so that every simulated physical qubit is measured and reset every two syndrome-extraction rounds, limiting a leakage episode to at most two rounds.

The supplement distinguishes this swap-type leakage-reduction unit from direct leakage-removal
gates and notes that the leaked qubit can still damage several neighbours within the two-round
interval.

## Leakage and partner channels [paper_fact]
Fact ID: ziad-leakage-partner-channel
Source locator: Methods, "Modelling leakage with Pauli Frame tracking," numbered items 1--4; Table 4, pp. 9--10
PDF page: 9
Claim: In the simulated channel, leakage depolarises the leaked qubit's Pauli register, a CZ involving one leaked qubit fully depolarises its sealed partner, relaxation returns a leaked qubit as maximally mixed and reset returns it to zero.

The two-qubit partner channel is a deliberately scalable Pauli-frame approximation. The leakage
probability and relaxation strength follow the values printed in Table 4.

## Leakage herald channel [paper_fact]
Fact ID: ziad-herald-channel
Source locator: Methods, "Modelling leakage with Pauli Frame tracking," numbered item 5; "Noise model and native gate set"; Table 4
PDF page: 10
Claim: Measurement can expose a leakage herald, with simulated herald error represented only by a false-negative probability of strength `5p` and false positives omitted.

The herald is a measurement-derived side channel. It reports that leakage occurred sometime since
the previous reset rather than revealing its exact gate-time location.

## Decoder inputs [paper_fact]
Fact ID: ziad-decoder-inputs
Source locator: Methods, "Decoding algorithm," opening paragraph
PDF page: 6
Claim: The Local Clustering Decoder receives a detector syndrome `S` and a set `P` of pre-grown graph edges supplied by the adaptivity engine.

Non-adaptive decoding uses no herald-triggered pre-grown set. An adaptive run starts with a
pre-clustering merge sequence whenever `P` is nonempty.

## Leakage-herald adaptation [paper_fact]
Fact ID: ziad-adaptivity-map
Source locator: Results, "Adaptivity engine," p. 4; Methods, "Leakage-aware decoding," p. 10; Supplementary Information, Appendix A.2, p. 2
PDF page: 4
Claim: For each possible leakage herald, the source precomputes edges made more likely by leakage since the prior reset and applies the simpler runtime approximation of pre-growing a minimal set of affected existing edges.

The supplement states that the runtime approximation assumes leakage immediately after the previous
reset. Pregrowing an edge is equivalent to assigning it zero weight in this unweighted clustering
implementation.

## Decoder computation [paper_fact]
Fact ID: ziad-decoder-computation
Source locator: Methods, "Decoding algorithm" and Boxes 1--2, pp. 6--7; Results, "Decoding engine"
PDF page: 6
Claim: The unweighted Local Clustering Decoder distributes graph vertices across FPGA processing elements and iterates growing, merging, picking and syncing stages until every cluster is even or reaches an open boundary.

Each vertex stores its cluster index, parent, radius, defect, parity, active and busy state. Edge
support is computed from endpoint radii rather than stored independently.

## Population comparison design [paper_fact]
Fact ID: ziad-population-comparison
Source locator: Figure 3 caption and surrounding Performance text; Zenodo `fpag_performance_data.csv`
PDF page: 5
Claim: Adaptive and non-adaptive unweighted LCD are compared on rotated-surface-code memory tasks at odd distances 5 through 17, using ten million simulated shots for every decoder, distance and low- or high-leakage condition.

The two regimes are low leakage (`p=10^-3`, `p_l=10^-4`) and high leakage
(`p=p_l=5 x 10^-4`). The archive contains aggregated shots, failures and state-machine cycle
averages but not the individual syndrome/herald records or random seeds.

## High-leakage result [paper_fact]
Fact ID: ziad-high-leakage-result
Source locator: Figure 3a legend and Performance text; Zenodo `fpag_performance_data.csv`
PDF page: 5
Claim: In the high-leakage model, the fitted suppression factor increases from `Lambda=2.12 +/- 0.00` without adaptivity to `3.85 +/- 0.03` with adaptivity, and the archived distance-17 rows contain 2,835 versus 11 failures in ten million shots.

These values compare the same declared code/noise condition and unweighted decoder family while
changing whether leakage-herald adaptations are applied.

## Low-leakage result [paper_fact]
Fact ID: ziad-low-leakage-result
Source locator: Figure 3a legend and Performance text; Zenodo `fpag_performance_data.csv`
PDF page: 5
Claim: In the low-leakage model, the fitted suppression factor increases from `Lambda=3.23 +/- 0.01` without adaptivity to `3.95 +/- 0.02` with adaptivity, and the archived distance-17 rows contain 139 versus 24 failures in ten million shots.

The source reports an improvement in both leakage proportions, with a larger scaling gain when
leakage is the dominant simulated mechanism.

## Suppression-fit reporting boundary [paper_fact]
Fact ID: ziad-lambda-fit-boundary
Source locator: Equation (1), p. 3; Figure 3a legend, p. 5; full Methods, Supplementary Information and Data Availability scope
PDF page: 5
Claim: Figure 3 reports numerical uncertainties for fitted `Lambda`, but the source bundle does not specify the fitting range, statistical estimator, resampling method or confidence level used to obtain them.

The public performance CSV supplies counts and shot totals from which new uncertainty analyses could
be performed, but such an analysis would be external to the source's reported method.

## Projected footprint result [paper_fact]
Fact ID: ziad-footprint-projection
Source locator: Performance discussion following Figure 3a
PDF page: 4
Claim: For a target error probability of `10^-6` in a `d x d x d` window under the high-leakage fit, the source projects distance 33 for non-adaptive decoding and distance 17 for adaptive decoding, corresponding to a near-75-percent physical-qubit reduction.

The source calls the window a proxy for a fundamental unit of lattice-surgery logic. Direct
simulation and FPGA implementation stop at distance 17, so the distance-33 requirement is an
extrapolation of the fitted scaling.

## FPGA decoder-engine timing [paper_fact]
Fact ID: ziad-fpga-timing
Source locator: Figure 3b, p. 5; Methods, "Hardware implementation details" and Table 3, p. 9
PDF page: 9
Claim: Decoder-state-machine cycle averages divided by the implementation clock frequency and code distance give reported decoder-engine times below one microsecond per round through distance 17 on XCVU19P and ZCU111 FPGAs for both adaptive and non-adaptive runs in both leakage regimes.

At distance 17, Table 3 gives XCVU19P times of 0.460 and 0.622 microseconds for
non-adaptive low/high leakage and 0.637 and 0.676 microseconds for adaptive low/high leakage. The
corresponding ZCU111 values are 0.558, 0.754, 0.773 and 0.820 microseconds.

These are cycle-derived decoder-engine values rather than an end-to-end streaming
trigger-to-correction timing measurement.

## Adaptivity timing boundary [paper_fact]
Fact ID: ziad-adaptivity-timing-boundary
Source locator: Performance text immediately following Figure 3b
PDF page: 5
Claim: The source explicitly does not measure execution time of the adaptivity engine that maps incoming trigger events to graph-edge updates.

The reported adaptive decoding times include the different clustering work caused by pre-grown
edges, but they are not an end-to-end trigger-to-correction latency measurement.

## FPGA resource reach [paper_fact]
Fact ID: ziad-fpga-resources
Source locator: Figure 3c, p. 5; Tables 1--2, pp. 8--9
PDF page: 8
Claim: At distance 17, the XCVU19P implementation uses 251,963 logic LUTs and 252,736 flip-flops, while the ZCU111 implementation uses 245,217 logic LUTs and 253,006 flip-flops.

These equal 6.17% and 3.09% of XCVU19P logic LUTs and flip-flops, and 57.66% and
29.75% of the corresponding ZCU111 resources. Power is not measured; the Discussion calls resource
utilisation a proxy for cost and power.

The tables give one total implementation row per distance and do not isolate incremental resource
cost for the adaptivity engine.

## Leakage-free accuracy comparator [paper_fact]
Fact ID: ziad-pymatching-comparator
Source locator: Methods, "Accuracy comparison with PyMatching"; Figure 6
PDF page: 7
Claim: Under a separate leakage-free uniform circuit-level depolarising model and standard non-wiggling schedule, the source reports thresholds near 0.55% for unweighted hardware LCD, 0.65% for weighted software LCD and 0.70% for PyMatching.

This comparison was added to benchmark the base clustering decoder against weighted MWPM. It does
not compare leakage-conditioned and leakage-blind decoding.

## Partner-depolarisation boundary [paper_fact]
Fact ID: ziad-partner-channel-boundary
Source locator: Methods, "Leakage-aware decoding"; peer-review author response to Reviewer 1, comment 4
PDF page: 10
Claim: The existing-edge adaptation relies on maximal depolarisation of a leaked qubit's sealed gate partner and does not apply unchanged when leakage merely erases the two-qubit gate without damaging that partner.

The author response names neutral-atom and ion settings as examples where different adaptations and
sampling are required. It characterises efficient large-scale treatment of those channels as open.

## Artifact boundary [paper_fact]
Fact ID: ziad-artifact-boundary
Source locator: Data Availability; Zenodo record `10.5281/zenodo.16982690`; peer-review code-availability exchange
PDF page: 10
Claim: The public archive supplies processed FPGA performance counts, leakage-enabled Stim circuits and leakage-free PyMatching benchmark data, while the modified Stim source, RTL/implementation source and raw syndrome/herald records are absent.

The authors state that some simulation artifacts are proprietary but do not identify the modified
Stim fork itself as the proprietary component. The reviewers and authors use different
reproducibility labels, while agreeing on the concrete absence of implementation source.

## No quantum-device record evaluation [literature_gap]
Fact ID: ziad-gap-quantum-device-records
Source locator: Abstract; Performance; Methods, "Modelling leakage with Pauli Frame tracking"; full Data Availability scope
PDF page: 1
Claim: This source does not evaluate leakage-conditioned decoding on syndrome or herald records produced by a quantum processor.
Gap scope: source_local

The physical noise, leakage carrier, measurement record and logical outcomes are sampled by the
modified Stim simulator; the FPGA is the decoder execution target.

## No documented identical-record pairing [literature_gap]
Fact ID: ziad-gap-identical-record-pairing
Source locator: Figure 3 caption; Zenodo performance CSV and archived file inventory
PDF page: 5
Claim: This source does not state that adaptive and non-adaptive decoder arms process identical sampled records or share random seeds.
Gap scope: source_local

It establishes common task distributions and equal shot totals but archives only aggregated results.

## No wrong-model robustness test [literature_gap]
Fact ID: ziad-gap-wrong-model-robustness
Source locator: Performance noise regimes; Methods noise model; peer-review author response to Reviewer 1, comment 4
PDF page: 4
Claim: This source does not freeze the adaptive decoder and test it under an incorrect leakage lifetime, partner channel, herald model, mixed mechanism or independently shifted calibration.
Gap scope: source_local

Both reported leakage regimes remain inside the declared SI1000-plus-leakage generator family.

## No frozen cross-setting transfer [literature_gap]
Fact ID: ziad-gap-frozen-transfer
Source locator: Discussion; hardware Tables 1--3; peer-review author response to Reviewer 1, comment 4
PDF page: 5
Claim: This source does not demonstrate a frozen leakage adaptation transferred without recompilation or retuning across an independent quantum device, code family or physically different carrier channel.
Gap scope: source_local

The two FPGA families test implementation portability for the same decoder construction, not
scientific transfer of the memory model or adaptation.
