+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2308.08186"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2308.08186v2"
source_artifact = "outputs/reading_packages/simulator_background_top10_2026-07-14/sources/2308.08186v2.pdf"
source_sha256 = "be54fe2ec199878855438bed58b4308172d02744cd8393f86765c151f25137fc"
title = "Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes Using Tensor Network Methods"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/MANABE_LEAKAGE_MPS_2308_08186_AUDIT_2026-08-05.md"
audit_packet_sha256 = "0b06d7c7a370817340c0f24536e30b2b587ed848aa5e364c51898e3d426bf9fe"
admission_status = "source_only_reviewed"
admission_reviewer = "/root"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

[[relations]]
predicate = "defines"
object_id = "manabe-phenomenological-qutrit-leakage-model"
object_type = "model"
object_label = "phenomenological qutrit leakage model"
fact_id = "msltn-qutrit-model-scope"

[[relations]]
predicate = "uses"
object_id = "manabe-qutrit-matrix-product-state"
object_type = "method"
object_label = "qutrit matrix-product state"
fact_id = "msltn-mps-carrier"

[[relations]]
predicate = "uses"
object_id = "manabe-sampled-kraus-pure-state-simulation"
object_type = "method"
object_label = "sampled Kraus pure-state simulation"
fact_id = "msltn-kraus-sampling"

[[relations]]
predicate = "measures"
object_id = "manabe-repeated-qec-logical-error-rate"
object_type = "observable"
object_label = "repeated-QEC logical error rate"
fact_id = "msltn-repetition-interface"

[[relations]]
predicate = "contradicts"
object_id = "manabe-gta-logical-rate-equivalence"
object_type = "model"
object_label = "general twirling approximation"
fact_id = "msltn-gta-result"

[[relations]]
predicate = "supports"
object_id = "manabe-leakage-removal-comparison"
object_type = "observable"
object_label = "leakage-removal comparison"
fact_id = "msltn-reset-logical-result"

[[relations]]
predicate = "limits"
object_id = "manabe-svd-computational-bottleneck"
object_type = "limitation"
object_label = "SVD bottleneck"
fact_id = "msltn-computational-cost"
+++
# Full-text review — Manabe, Suzuki, and Darmawan, arXiv:2308.08186v2

## Source identity [paper_fact]
Fact ID: msltn-source-identity
Source locator: PDF page 1, title, author block, abstract, and visible arXiv version stamp
PDF page: 1
Claim: The fixed source is the 15-page arXiv:2308.08186v2 preprint “Efficient Simulation of Leakage Errors in Quantum Error Correcting Codes Using Tensor Network Methods” by Hidetaka Manabe, Yasunari Suzuki, and Andrew S. Darmawan, with a visible version date of 21 January 2025 and Appendix A included in the same PDF.

## Selection scope [paper_fact]
Fact ID: msltn-selection-scope
Source locator: Abstract; Sec. I closing paragraphs; Sec. IV opening paragraphs
PDF page: 1
Claim: The source studies whether a matrix-product-state simulator can propagate declared qutrit leakage processes through repeated one-dimensional repetition-code and thin-surface-code circuits, compare leakage-removal strategies, and estimate decoded logical error rates without replacing the coherent leakage channel by a twirled surrogate.

The executed code families are selected for one-dimensional or quasi-one-dimensional entanglement
structure rather than as an exhaustive set of quantum error-correcting codes.

## Phenomenological qutrit-model scope [paper_fact]
Fact ID: msltn-qutrit-model-scope
Source locator: Sec. II opening paragraphs
PDF page: 2
Claim: The source represents superconducting qubits by a phenomenological qutrit leakage model intended to capture coherence and leakage spreading but explicitly not intended to correspond to a specific experimental noise process.

The modeled basis contains the computational states and one leaked state. Architecture-specific
models are said to be incorporable at potentially higher computational cost, but they are not
instantiated in this source.

## Coherent single-qutrit control leakage [paper_fact]
Fact ID: msltn-control-leakage
Source locator: Sec. II.A, Eqs. (1)--(5)
PDF page: 2
Claim: The single-qutrit control-error model composes rotations in the `|0>`--`|2>` and `|1>`--`|2>` subspaces with a leaked-state phase, using rotation strength `theta` and qubit-specific phases `lambda_i` and `phi_i` drawn from `[0, 2 pi)`.

The construction assumes independent Rabi processes for the two computational-to-leakage
transitions and a far-detuned description of leaked-state oscillation.

## Leakage-conditioned two-qutrit gates and spreading [paper_fact]
Fact ID: msltn-two-qutrit-leakage
Source locator: Sec. II.B, Eqs. (6)--(7) and leakage-spreading paragraph
PDF page: 3
Claim: The modeled two-qutrit gate is ideal in the computational subspace, adds a phase `i` when the control occupies `|2>`, and is followed by four `Y`-axis rotations with angle `theta_spread` that coherently transfer a neighbouring computational-subspace state toward `|22>` when one partner is leaked.

The `pi/2` leaked-state phase and the reduced four-rotation spreading model are phenomenological
choices motivated by cited superconducting-qubit observations.

## Binary measurement instrument [paper_fact]
Fact ID: msltn-measurement-instrument
Source locator: Sec. II.C, Eqs. (8)--(9)
PDF page: 3
Claim: The binary CP instrument projects computational states onto their corresponding outcome and assigns leaked-state population to outcomes zero and one with probabilities `p` and `1-p`, with `p = 0.5` in the simulations.

The source neglects measurement-induced leakage and instead focuses its numerical models on CZ and
thermal leakage.

## Round-local thermal channel [paper_fact]
Fact ID: msltn-thermal-channel
Source locator: Sec. II.D, Eq. (10) and following parameter paragraph
PDF page: 3
Claim: The thermal-noise arm truncates a harmonic-oscillator amplitude-damping and excitation master equation to obtain a qutrit Kraus CPTP map, integrates it for `tau = 1.0 microsecond`, and applies that reduced map to every qutrit at the beginning of each syndrome-measurement round.

The numerical parameters use a 10 GHz resonance, temperature `T` in mK, and coupling `gamma` in
MHz. The environment itself is not included in the propagated state.

## Qutrit MPS as the propagated state [paper_fact]
Fact ID: msltn-mps-carrier
Source locator: Sec. III.A--B, Eq. (11), Fig. 1, and opening simulation paragraph
PDF page: 4
Claim: The simulation carries the joint data-and-ancilla pure state through many error-correction rounds as a qutrit matrix-product state whose bond dimension `chi` bounds the bipartite entanglement representable across any chain cut.

Gates, dissipative branches, and measurements modify this same state throughout the circuit; a
leaked-state amplitude or population therefore remains in the propagated system state until a later
modeled operation changes it.

## Canonical MPO and SVD update [paper_fact]
Fact ID: msltn-mpo-svd-update
Source locator: Sec. III.B and Fig. 1; Appendix A, Eqs. (A1)--(A8)
PDF page: 4
Claim: A two-qutrit operation is represented as an MPO across the sites between its targets, contracted sequentially into a canonical MPS, and split by SVD while small singular values are discarded to restore the chosen bond dimension.

Single-site operations update one tensor directly. For a non-neighbouring two-site gate, identity
MPO tensors connect the targets, so cost grows with separation in the selected MPS ordering.

## Sampled Kraus pure-state evolution [paper_fact]
Fact ID: msltn-kraus-sampling
Source locator: Appendix A, Eq. (A9) and closing paragraph
PDF page: 15
Claim: The sampled Kraus pure-state simulation chooses Kraus operator `K_i` with probability `Tr(K_i |psi><psi| K_i^dagger)`, applies the selected operator as a one-site update, and treats projective measurements in the same branch-sampling manner.

The reported ensemble quantities are therefore estimated from repeated sampled pure-state runs
rather than from a deterministically propagated density operator.

## Repetition-code QEC interface [paper_fact]
Fact ID: msltn-repetition-interface
Source locator: Sec. IV.A and Fig. 2
PDF page: 5
Claim: For a distance-`d` repetition code, the source initializes logical `|0>` or `|1>`, executes `d` noisy syndrome-measurement rounds on `2d-1` data-plus-ancilla qutrits, measures all data qutrits, and uses minimum-weight perfect matching on syndrome and final-data outcomes to estimate a repeated-QEC logical error rate.

The logical-error event is defined as decoding failure.

## Thin-surface-code interface and geometry [paper_fact]
Fact ID: msltn-thin-surface-interface
Source locator: Sec. IV.A and Fig. 3
PDF page: 5
Claim: The thin-surface-code calculation uses a `3 x d` quasi-one-dimensional layout with `6d-1` data-plus-ancilla qutrits, a snake-ordered MPS, and syndrome-gate MPOs of length up to six, and it reports logical `Z` and `X` error probabilities after decoding.

Increasing `d` increases only the source's `Z` distance; the minimum `X`-logical length remains
fixed, so the two logical-error components need not improve together.

## Low-entanglement initialization and width cost [paper_fact]
Fact ID: msltn-initial-bond-and-width
Source locator: Sec. IV.A, paragraphs describing MPS ordering and wider strips
PDF page: 6
Claim: The initialized repetition-code state has `chi = 1`, the initialized logical `|+>` state of the `3 x d` thin surface code has maximum `chi = 4`, and the source states that width-five and width-seven logical states require at most `chi = 8` and `16` while their gate MPO lengths increase to ten and fourteen.

The width-five and width-seven statements concern representability and anticipated resource growth;
the paper does not present repeated-QEC numerical results for those widths.

## Leakage-removal operations [paper_fact]
Fact ID: msltn-reset-operations
Source locator: Sec. IV.B, Eq. (12) and Fig. 4
PDF page: 6
Claim: The no-reset map returns computational-basis ancilla outcomes to `|0>` while preserving leaked population in `|2>`, MLR maps every ancilla state perfectly to `|0>`, and DQLR applies MLR, a data--ancilla LeakageISWAP printed as acting in the `|11>`--`|20>` subspace, and a second MLR.

MLR acts only on ancillas; DQLR is introduced to remove data-qutrit leakage by moving it to an
ancilla that is then reset. The following source sentence inconsistently says that the gate converts
`|02>` to `|11>`; this review preserves rather than resolves that ket-ordering anomaly.

## Truncation control [paper_fact]
Fact ID: msltn-truncation-threshold
Source locator: Sec. V.A opening paragraphs and Figs. 5--7; Appendix A after Eq. (A6)
PDF page: 7
Claim: The bond dimension is chosen dynamically so that the 2-norm of the singular values discarded at each SVD does not exceed `10^-6` for repetition-code calculations or `10^-4` for thin-surface-code calculations, thresholds the source says were sufficient for logical rates in the studied parameter regions.

The source does not give a global accumulated state-error or record-distribution bound derived from
these local thresholds.

## Sampling and processor report [paper_fact]
Fact ID: msltn-sampling-resources
Source locator: Sec. V opening paragraph
PDF page: 7
Claim: The tensor-network calculations use the TensorNetwork Python library on an Intel Xeon Platinum 9242 system with 96 threads, and the main Results prose states that each plotted data point averages ten thousand samples.

Figure 11 later describes its logical rates as based on “several thousand” samples, so the source
does not give one unambiguous sample count for every displayed point.

## Repetition-code bond-dimension behavior [paper_fact]
Fact ID: msltn-repetition-bond-result
Source locator: Sec. V.A and Figs. 5--6
PDF page: 7
Claim: In the distance-99, 99-round repetition-code calculations, reported average bond dimensions remain below 65 across the displayed parameter grid, increase during early rounds and then saturate, increase with coherent leakage, and decrease when stronger leakage removal is used.

For long runs, the source reports approximate independence from `d` outside finite-size effects for
`d` below about 50 and interprets this numerical behavior as an area-law indication, not as a proved
bound for arbitrary noise or codes.

## Thin-code bond-dimension behavior [paper_fact]
Fact ID: msltn-thin-bond-result
Source locator: Sec. V.A and Fig. 7
PDF page: 8
Claim: For the displayed `3 x 7` thin-surface-code runs over seven rounds, maintaining the `10^-4` local truncation threshold requires average bond dimensions between about 9 and 21 over the plotted rotation, bath-coupling, and reset settings.

The source notes that this run has not reached a saturation regime and is more costly than the
repetition-code calculation.

## General twirling approximation [paper_fact]
Fact ID: msltn-gta-definition
Source locator: Sec. V.B, Eqs. (13)--(20)
PDF page: 8
Claim: The general twirling approximation constructs an incoherent channel from the coherent control-leakage unitary's leakage and seepage rates, retains a projected computational-subspace action before Pauli twirling it, and removes leakage coherence from the surrogate channel.

The exact-versus-surrogate comparison sets leakage spreading to zero.

## GTA logical-rate discrepancy [paper_fact]
Fact ID: msltn-gta-result
Source locator: Sec. V.B, Fig. 8 and first paragraph on the following page
PDF page: 8
Claim: For the displayed distance-19 repetition-code setting, the general twirling approximation produces a substantially different logical-error curve from the coherent channel and overestimates the logical error by more than a factor of three in the MLR case.

The source concludes from this example that leakage and seepage rates alone need not preserve the
logical effect of the coherent leakage process.

## Leakage-removal comparison [paper_fact]
Fact ID: msltn-reset-logical-result
Source locator: Sec. V.C and Figs. 9--11
PDF page: 9
Claim: The leakage-removal comparison shows that no reset, ancilla-only MLR, and DQLR can yield markedly different repetition-code logical-error curves under the same declared leakage model, with DQLR suppressing the large-distance damage caused by persistent control leakage and leakage spreading in the plotted regimes.

At low temperature and small damping, no reset and MLR can worsen at larger distance because leaked
population persists and spreads; increasing damping can instead return population toward the
computational subspace and produce non-monotonic logical behavior.

## Finite-sampling floor [paper_fact]
Fact ID: msltn-finite-sampling-floor
Source locator: Fig. 11 caption
PDF page: 10
Claim: Figure 11 plots only logical-error estimates above `3 x 10^-4` and reports zero observed logical failures for the DQLR runs at distances 49 and 99 in the sampled data.

The zero event count is a finite-sampling statement and is not reported as a certified zero logical
error rate.

## Thin-surface-code logical result [paper_fact]
Fact ID: msltn-thin-logical-result
Source locator: Sec. V.C closing paragraphs and Fig. 12
PDF page: 10
Claim: The executed thin-surface-code study reports logical `Z` and `X` error curves through `d = 19` for no reset and MLR, with leakage spreading disabled, and finds that stronger modeled removal suppresses the displayed logical effect while large distance and weak damping can remove the apparent logical-`Z` threshold behavior.

The source anticipates similar behavior in a standard `d x d` surface code but does not simulate
that geometry.

## Surface-code comparator omissions [paper_fact]
Fact ID: msltn-thin-omissions
Source locator: Sec. V.C final two paragraphs before the Conclusion
PDF page: 10
Claim: Because of simulation cost and procedural complexity, the thin-surface-code calculations omit leakage spreading and DQLR and compare only no reset with MLR.

These omissions make the repetition-code three-arm comparison broader than the thin-surface-code
comparison.

## Computational-cost boundary [paper_fact]
Fact ID: msltn-computational-cost
Source locator: Sec. IV.A width discussion; Sec. V.C closing cost paragraph
PDF page: 10
Claim: The source identifies nonlocal MPO length as a principal resource constraint, calls the SVD bottleneck crucial for thin-code simulations at `d >= 5`, and states that larger studies would require massive cluster parallelization or faster GPU SVD.

It reports neither wall-clock time nor peak memory for the displayed calculations.

## Full two-dimensional reach boundary [paper_fact]
Fact ID: msltn-full-2d-boundary
Source locator: Sec. IV.A opening scope paragraph; Sec. VI closing paragraph
PDF page: 5
Claim: A full two-dimensional surface code is outside the demonstrated scope; the source leaves codes with more complex connectivity to future tensor-network ansatzes such as PEPS or isoTNS.

The phrase “several hundred qudits” therefore refers to the executed one-dimensional and
quasi-one-dimensional geometries, not generic two-dimensional code patches.

## Retained-environment boundary [literature_gap]
Fact ID: msltn-gap-retained-environment
Source locator: Sec. II.D and Appendix A, complete dissipative-evolution construction
PDF page: 3
Claim: The source does not retain an explicit bath or environment state across syndrome rounds; it applies a reduced single-qutrit CPTP map at the beginning of each round and samples that map's Kraus branches.
Gap scope: source_local

The system qutrit state can carry leakage between rounds, but this source does not establish an
environment-mediated memory kernel or strict quantum non-Markovianity.

## Physical intervention-cost boundary [literature_gap]
Fact ID: msltn-gap-physical-reset-cost
Source locator: Sec. IV.B and complete Results comparison of no reset, MLR, and DQLR
PDF page: 6
Claim: The source does not report a physical duration, gate infidelity, reset failure, calibration burden, qubit overhead, or hardware measurement for its modeled MLR and DQLR operations.
Gap scope: source_local

Its cost discussion concerns simulation resources rather than the physical overhead of executing a
leakage-removal protocol.

## Global numerical-certificate boundary [literature_gap]
Fact ID: msltn-gap-global-certificate
Source locator: Sec. V.A and Appendix A, complete truncation and sampling discussion
PDF page: 7
Claim: The source does not derive a global error bound from its per-SVD discarded-singular-value thresholds or separately certify finite-sample and MPS-truncation error in the reported logical-error estimates.
Gap scope: source_local

The source's accuracy statement is empirical and restricted to the parameter regions studied.

## Hardware and transfer boundary [literature_gap]
Fact ID: msltn-gap-hardware-transfer
Source locator: Abstract; Sec. II opening scope paragraphs; Secs. V--VI
PDF page: 1
Claim: The source does not observe leakage on hardware, fit its phenomenological model to a device, or demonstrate that the reported logical or reset-strategy conclusions transfer beyond the modeled code geometries, noise family, parameters, and decoder.
Gap scope: source_local
