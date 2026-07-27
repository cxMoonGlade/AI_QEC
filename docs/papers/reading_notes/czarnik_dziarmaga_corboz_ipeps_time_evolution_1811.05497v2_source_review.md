+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1811.05497"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1811.05497v2"
source_artifact = "docs/papers/1811.05497v2.pdf"
source_sha256 = "a29c4bf23e381c50cae91a708456d6240792302bf1c0e127348cd2c6fdc5639c"
title = "Time Evolution of an Infinite Projected Entangled Pair State: an Efficient Algorithm"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/CZARNIK_DZIARMAGA_CORBOZ_1811_05497V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "8cbca6a0b180a78ac566ec3bf31b211d32e7a53a427f2b586de598e2b8bc71d6"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-czarnik-1811.05497v2-2026-07-27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

[[relations]]
predicate = "defines"
object_id = "czarnik-ipeps-bond-growth-compression-step"
object_type = "method"
object_label = "iPEPS bond-growth-and-compression step"
fact_id = "czarnik1811-bond-growth-compression"

[[relations]]
predicate = "uses"
object_id = "czarnik-one-bond-auxiliary-ipeps"
object_type = "method"
object_label = "one-bond auxiliary iPEPS"
fact_id = "czarnik1811-local-auxiliary-state"

[[relations]]
predicate = "defines"
object_id = "czarnik-global-fidelity-objective"
object_type = "observable"
object_label = "global fidelity objective"
fact_id = "czarnik1811-global-fidelity-objective"

[[relations]]
predicate = "uses"
object_id = "czarnik-local-bond-fidelity-objective"
object_type = "observable"
object_label = "local bond-fidelity objective"
fact_id = "czarnik1811-local-bond-fidelity"

[[relations]]
predicate = "uses"
object_id = "czarnik-ctmrg-bond-environment"
object_type = "method"
object_label = "CTMRG bond environment"
fact_id = "czarnik1811-ctmrg-environment"

[[relations]]
predicate = "limits"
object_id = "czarnik-finite-real-time-convergence-horizon"
object_type = "limitation"
object_label = "finite real-time convergence horizon"
fact_id = "czarnik1811-real-time-entanglement-barrier"

[[relations]]
predicate = "measures"
object_id = "czarnik-thermal-critical-temperature-scaling"
object_type = "observable"
object_label = "thermal critical-temperature scaling"
fact_id = "czarnik1811-critical-scaling"

[[relations]]
predicate = "uses"
object_id = "czarnik-simple-update-truncation"
object_type = "method"
object_label = "simple-update truncation"
fact_id = "czarnik1811-simple-update"

[[relations]]
predicate = "uses"
object_id = "czarnik-reduced-tensor-optimization"
object_type = "method"
object_label = "reduced-tensor optimization"
fact_id = "czarnik1811-reduced-tensor-cost"

[[relations]]
predicate = "measures"
object_id = "czarnik-reported-full-update-cpu-workload"
object_type = "observable"
object_label = "reported full-update CPU workload"
fact_id = "czarnik1811-cpu-runtime"
+++
# Full-text review — Czarnik, Dziarmaga, and Corboz, arXiv:1811.05497v2

## Source identity [paper_fact]
Fact ID: czarnik1811-source-identity
Source locator: Title page, author block, date, and arXiv version footer
PDF page: 1
Claim: The reviewed source is the 13-page arXiv:1811.05497v2 preprint by Piotr Czarnik, Jacek Dziarmaga, and Philippe Corboz on time evolution of an infinite projected entangled pair state.

The title page is dated 15 January 2019, while the arXiv footer identifies v2
and 14 January 2019.

## Evolution scope [paper_fact]
Fact ID: czarnik1811-evolution-scope
Source locator: PDF page 1, Abstract
PDF page: 1
Claim: The source presents iPEPS algorithms for real, Lindbladian, and imaginary-time evolution and benchmarks them on two-dimensional quantum Ising workloads.

The thermal-state calculations use a purification and optionally unitary
ancilla disentanglers. The dynamical examples are presented as
proof-of-principle simulations.

## Bond growth and compression [paper_fact]
Fact ID: czarnik1811-bond-growth-compression
Source locator: Sec. II, opening paragraph
PDF page: 1
Claim: The source defines an iPEPS bond-growth-and-compression step in which a nearest-neighbour gate enlarges its acted bond from \(D\) to \(kD\), with \(k\le d^2\), before the post-step iPEPS is approximated with the original bond dimension \(D\).

Here \(d\) is the local site dimension and \(D\) is the retained virtual bond
dimension. The abstract denotes the enlarged value generically by \(D'>D\).

## One-bond auxiliary state [paper_fact]
Fact ID: czarnik1811-local-auxiliary-state
Source locator: Sec. II, first two paragraphs
PDF page: 2
Claim: The efficient update constructs a one-bond auxiliary iPEPS \(\lvert\widetilde\psi''\rangle\) that equals the exact enlarged state \(\lvert\psi'\rangle\) everywhere except at one acted bond, where two tensors with bond \(D\) replace the enlarged tensors.

After optimizing the two auxiliary tensors, the source uses them on all
equivalent nearest-neighbour pairs to construct the global
\(\lvert\psi''\rangle\).

## Finite real-time convergence horizon [paper_fact]
Fact ID: czarnik1811-real-time-entanglement-barrier
Source locator: Sec. II, paragraph beginning “A challenging application”
PDF page: 2
Claim: The source identifies a finite real-time convergence horizon for fixed-resource tensor networks because a generic sudden quench creates separating entangled quasiparticle pairs and asymptotically linear entanglement-entropy growth.

The paper says a tensor network is consequently expected to fail after a
certain finite evolution time. It contrasts this with localized excitations or
local dissipation, which can slow the growth.

## Thermal purification and gauge [paper_fact]
Fact ID: czarnik1811-thermal-purification
Source locator: Sec. III.A, Eqs. (2)–(5)
PDF page: 3
Claim: The source represents the Gibbs operator by tracing ancillas from an iPEPS purification and uses an arbitrary unitary ancilla gauge \(G(\beta)\) as a disentangler intended to reduce the required bond dimension.

The purification begins from on-site maximally correlated spin–ancilla pairs at
\(\beta=0\). The gauge cancels when the ancillas are traced from the Gibbs
operator.

## Suzuki–Trotter gate layers [paper_fact]
Fact ID: czarnik1811-trotter-decomposition
Source locator: Secs. III.B–III.C, Eqs. (6)–(10)
PDF page: 3
Claim: The source uses a second-order Suzuki–Trotter step whose Ising interaction is split into four commuting horizontal and vertical nearest-neighbour gate layers on a two-sublattice checkerboard.

The one-site field gates act directly on physical tensor indices. The remainder
of the construction is presented for one representative horizontal gate layer.

## Ising-gate bond doubling [paper_fact]
Fact ID: czarnik1811-zz-gate-bond-doubling
Source locator: Sec. III.D, Eq. (11) and Fig. 2(b,c)
PDF page: 4
Claim: The displayed Ising \(ZZ\) gate has a two-term local factorization, so contracting its factors into \(A,B\) produces exact post-gate tensors \(A',B'\) joined by a bond of dimension \(2D\).

Equation (11) sums over \(\mu=0,1\), with
\(z_{j,\mu}=\sqrt{\Lambda_\mu}(Z_j)^\mu\),
\(\Lambda_0=\cos d\tau\), and \(\Lambda_1=i\sin d\tau\).

## Global fidelity objective [paper_fact]
Fact ID: czarnik1811-global-fidelity-objective
Source locator: Sec. III.E, Eq. (12)
PDF page: 4
Claim: The source prints a global fidelity objective \(F=\langle\psi''|\psi'\rangle\langle\psi'|\psi''\rangle/\langle\psi''|\psi''\rangle\) for direct optimization of the global \(D\)-bond approximation against the enlarged target.

The source says direct maximization is feasible and should be most accurate in
principle, but is not its most efficient approach.

## Local bond-fidelity objective [paper_fact]
Fact ID: czarnik1811-local-bond-fidelity
Source locator: Sec. III.E, Eq. (13)
PDF page: 4
Claim: The efficient method instead maximizes a local bond-fidelity objective \(\widetilde F=\langle\widetilde\psi''|\psi'\rangle\langle\psi'|\widetilde\psi''\rangle/\langle\widetilde\psi''|\widetilde\psi''\rangle\) over \(A'',B''\), and optionally \(g\).

The auxiliary network differs from the enlarged target at only the optimized
bond.

## Local-to-global tensor placement [paper_fact]
Fact ID: czarnik1811-local-to-global-placement
Source locator: Sec. III.E, paragraph following Eq. (13)
PDF page: 4
Claim: After local convergence, the source places \(A'',B''\) at every equivalent site and explicitly calls this global placement an approximation relative to direct global optimization.

The source argues that the surrounding enlarged-state environment should
preserve accuracy when \(D\) is already large enough to make truncation errors
negligible.

## CTMRG bond environment [paper_fact]
Fact ID: czarnik1811-ctmrg-environment
Source locator: Sec. III.E, final paragraph
PDF page: 4
Claim: The rank-six CTMRG bond environment used by the local objective is obtained approximately with environmental bond dimension \(\chi\).

The source calls \(\chi\) a refinement parameter.

## CTMRG bottleneck [paper_fact]
Fact ID: czarnik1811-ctmrg-bottleneck
Source locator: Sec. III.E, opening paragraphs
PDF page: 5
Claim: The source reports that all following results were checked for convergence with increasing \(\chi\) and identifies CTMRG as the algorithm's numerical-cost bottleneck.

This is a source-reported numerical convergence practice, not an analytic
contraction guarantee.

## Reused local environment [paper_fact]
Fact ID: czarnik1811-reused-local-environment
Source locator: Sec. III.E, paragraph preceding Sec. III.F
PDF page: 5
Claim: The local optimization reuses one tensor environment because the overlaps in Eq. (13) have the same environment, independent of \(A'',B''\), and the disentangler \(g\).

For the disentangler, bra and ket copies cancel on every bond except the
optimized one, so they add no leading CTMRG cost in the source's analysis.

## Disentangler SVD update [paper_fact]
Fact ID: czarnik1811-disentangler-svd-update
Source locator: Sec. III.F, Eq. (15) and following sentence
PDF page: 5
Claim: For fixed \(A'',B''\), the source updates the unitary disentangler as \(g=uv^\dagger\), where \(u,v\) come from a singular value decomposition of its tensor environment \(E(g)\).

This is the source's local polar-factor update for the ancilla gauge.

## Iterative local optimizer [paper_fact]
Fact ID: czarnik1811-local-optimization-loop
Source locator: Sec. III.F, Eq. (18) and opening paragraph
PDF page: 6
Claim: The source updates \(A''\) and \(B''\) with metric pseudoinverses and repeats the loop \(\cdots\rightarrow g\rightarrow A''\rightarrow B''\rightarrow\cdots\) until self-consistency and convergence of \(\widetilde F\).

Actual calculations optimize reduced tensors rather than the full tensors.

## Previous-environment error concern [paper_fact]
Fact ID: czarnik1811-old-environment-error-concern
Source locator: Sec. III.G, first two paragraphs
PDF page: 6
Claim: Before presenting benchmarks, the source gives a simple error-propagation argument under which replacing the enlarged \(\lvert\psi'\rangle\) environment by the previous \(\lvert\psi\rangle\) environment creates a final-state error that need not vanish as \(d\beta\) decreases.

The argument assumes the environment error and induced state error are each
linear in \(d\beta\), and that errors from intermediate steps add.

## Pure-state real-time reduction [paper_fact]
Fact ID: czarnik1811-real-time-fu-reduction
Source locator: Sec. III.H
PDF page: 6
Claim: For pure-state real-time evolution, unitary gates cancel from the local-overlap environment outside the optimized bond, so the source's eeFU construction reduces to the FU algorithm.

The transfer-tensor indices then retain dimension \(D^2\), reducing the
CTMRG cost relative to an enlarged-bond environment.

## Real-time quench benchmark [paper_fact]
Fact ID: czarnik1811-real-time-benchmark
Source locator: Fig. 5 and Sec. IV.A
PDF page: 6
Claim: For the three reported Ising quenches, increasing \(D=2,\ldots,8\) improves energy conservation and extends the time range over which transverse magnetization appears converged.

The slowest convergence occurs at the gapless quantum critical field; the
near-classical small-field quench converges fastest.

## Lindblad vectorization [paper_fact]
Fact ID: czarnik1811-lindblad-vectorization
Source locator: Sec. IV.B, Eqs. (19)–(20)
PDF page: 7
Claim: The source adapts the real-time algorithm to ensemble Lindblad evolution by representing a vectorized density matrix as an iPEPS isomorphic to an iPEPO density operator.

The benchmark uses a transverse-field Ising Hamiltonian and local spin-lowering
operators at fixed parameters.

## Lindbladian benchmark [paper_fact]
Fact ID: czarnik1811-lindblad-benchmark
Source locator: Fig. 6 and following paragraph
PDF page: 7
Claim: In the reported dissipative Ising example, the longitudinal-magnetization curves appear converged over an increasing time range as \(D\) increases from 4 to 7.

The source describes this as a proof-of-principle simulation.

## Near-critical contraction cost [paper_fact]
Fact ID: czarnik1811-near-critical-cost
Source locator: Sec. IV.C, paragraph beginning “We observe”
PDF page: 8
Claim: The source reports very slow CTMRG convergence and strong time-step sensitivity near the thermal critical point, and introduces a small longitudinal bias \(h_z\) to move the simulated state away from criticality.

The final critical estimates extrapolate results obtained at nonzero bias
toward \(h_z=0\).

## Thermal critical-temperature scaling [paper_fact]
Fact ID: czarnik1811-critical-scaling
Source locator: Sec. IV.D, Eqs. (21)–(23)
PDF page: 8
Claim: The source defines thermal critical-temperature scaling through the bias dependence \(T^*-T_c\sim h_z^{1/\widetilde\beta\delta}\) of peaks in the order-parameter derivative.

The symbol \(\widetilde\beta\) denotes a critical exponent and is distinct from
inverse temperature \(\beta\).

## Critical estimate at \(h_x=2.5\) [paper_fact]
Fact ID: czarnik1811-critical-result-hx25
Source locator: Fig. 9 and final paragraph of Sec. IV.D
PDF page: 8
Claim: At \(h_x=2.5\), \(D=5\), and \(5\times10^{-4}\le h_z\le0.01\), the source reports \(T_c=1.2745(7)\) and \(1/\widetilde\beta\delta=0.549(4)\), with \(d\beta=0.002\) and \(\chi=25\) judged converged.

The cited QMC comparison is \(T_c=1.2737(6)\). The QMC number is external
reference data, not a computation reproduced in the source.

## Critical estimate at \(h_x=2.9\) [paper_fact]
Fact ID: czarnik1811-critical-result-hx29
Source locator: Fig. 10 and opening paragraph
PDF page: 9
Claim: At \(h_x=2.9\), \(D=5\), and \(5\times10^{-4}\le h_z\le0.01\), the source reports \(T_c=0.6055(10)\) and \(1/\widetilde\beta\delta=0.563(4)\), with \(d\beta=0.005\) and \(\chi=25\) judged converged.

The source reports the temperature estimate within \(0.5\%\) of the cited QMC
value \(0.6085(8)\).

## Disentangler resource tradeoff [paper_fact]
Fact ID: czarnik1811-disentangler-resource-tradeoff
Source locator: Sec. IV.E, final paragraph
PDF page: 9
Claim: The source reports that ancilla disentanglers can improve fixed-\(D\) accuracy at the price of more iterations of the local optimization loop and larger reduced tensors.

## Disentangler accuracy benchmark [paper_fact]
Fact ID: czarnik1811-disentangler-benchmark
Source locator: Table I and caption
PDF page: 10
Claim: For the reported \(h_x=2.9\) thermal fit, disentanglers improve the \(D=4\) critical estimates by about one order of magnitude, while the \(D=5\) eeFU and eeFUd estimates have similar accuracy.

The comparison uses the same larger reduced tensors in both arms to make the
time-evolution comparison more direct.

## Previous- versus enlarged-environment benchmark [paper_fact]
Fact ID: czarnik1811-fu-eefu-comparison
Source locator: Fig. 12, Table II, and Sec. IV.F
PDF page: 10
Claim: For the two reported bias-smoothed thermal Ising fits, the cheaper previous-state-environment FU method and the enlarged-state-environment eeFU method give similar magnetization and statistically compatible fitted critical data.

The source calls the result numerical evidence. It does not claim a general
equivalence of the two formulations.

## Simple-update truncation [paper_fact]
Fact ID: czarnik1811-simple-update
Source locator: Sec. IV.G, opening paragraph
PDF page: 10
Claim: The source defines simple-update truncation as reducing an enlarged \(kD\) bond by an SVD of the tensor pair while ignoring long-range correlations in the bond environment.

Simple update permits larger \(D\) because CTMRG is then required only to
evaluate observables in the final state.

## Simple- versus full-update benchmark [paper_fact]
Fact ID: czarnik1811-su-fu-comparison
Source locator: Table III and surrounding discussion
PDF page: 11
Claim: In the reported \(h_x=2.9\) example, \(D=12\) simple update takes longer and gives substantially poorer critical estimates than \(D=5\) full update.

The source limits its conclusion that FU outperforms SU to the present example.

## Reduced-tensor optimization [paper_fact]
Fact ID: czarnik1811-reduced-tensor-cost
Source locator: Appendix A, Eqs. (A1)–(A3)
PDF page: 12
Claim: The implementation uses reduced-tensor optimization, with the stated spin-\(1/2\) element counts changing from \(4D^4\) for a full tensor to \(16D^2\) with disentanglers or \(4D^2\) without them.

The QR isometries are held fixed during the local optimization, and only the
reduced tensors are varied.

## CTMRG stopping rule [paper_fact]
Fact ID: czarnik1811-ctmrg-stopping-rule
Source locator: Appendix B, first two sentences
PDF page: 12
Claim: The source stops CTMRG when the relative per-iteration change in the two-site reduced-tensor environment's 2-norm is below \(10^{-10}\).

This is the printed iterative convergence criterion.

## Reported CPU workload [paper_fact]
Fact ID: czarnik1811-cpu-runtime
Source locator: Appendix B, final sentence
PDF page: 12
Claim: The reported full-update CPU workload for the \(h_x=2.9\), \(D=5\) critical estimates is 5–6 days on a 14-core 2.20 GHz Intel Xeon Gold 5120 processor.

No peak-memory value accompanies the wall-time statement.

## Fidelity normalization convention [literature_gap]
Fact ID: czarnik1811-gap-fidelity-normalization
Source locator: Sec. III.E, Eqs. (12)–(13)
PDF page: 4
Claim: The source calls \(F\) and \(\widetilde F\) fidelities but does not state a target-state normalization convention or include \(\langle\psi'|\psi'\rangle\) in either printed denominator.
Gap scope: source_local

Because the target is fixed during an update, a target-only factor would not
change the optimizer. The printed objectives nevertheless do not by themselves
define an absolute normalized fidelity value.

## Missing local-to-global guarantee [literature_gap]
Fact ID: czarnik1811-gap-local-global-guarantee
Source locator: Sec. III.E, paragraph following Eq. (13)
PDF page: 4
Claim: The source does not prove that maximizing the one-bond \(\widetilde F\) maximizes global \(F\), nor derive an accumulated state-error bound for repeated local-to-global tensor placement.
Gap scope: source_local

Its accuracy argument assumes \(D\) is large enough to make truncation errors
negligible and is supported by later workload-specific benchmarks.

## Missing CTMRG error certificate [literature_gap]
Fact ID: czarnik1811-gap-ctmrg-error-certificate
Source locator: Sec. III.E, CTMRG convergence paragraph
PDF page: 5
Claim: The source does not convert finite-\(\chi\) CTMRG convergence into a certified state-fidelity or observable-error bound.
Gap scope: source_local

The reported \(\chi\)-scans and iterative stopping rule are numerical
diagnostics.

## Missing universal real-time horizon law [literature_gap]
Fact ID: czarnik1811-gap-real-time-horizon
Source locator: Sec. II, real-time evolution paragraph
PDF page: 2
Claim: The source does not derive a universal quantitative law for reachable real time as a function of \(D\), model parameters, or target error.
Gap scope: source_local

The paper gives a qualitative entanglement-growth argument and empirical
convergence windows.

## Missing selective measurement instrument [literature_gap]
Fact ID: czarnik1811-gap-selective-instrument
Source locator: Sec. IV.B, Lindblad equation and vectorization
PDF page: 7
Claim: The source evolves an ensemble density operator and does not define an outcome-resolved selective measurement instrument or sampled quantum trajectory.
Gap scope: source_local

Expectation-value evolution is not an outcome-conditioned instrument.

## Missing reset transaction [literature_gap]
Fact ID: czarnik1811-gap-reset
Source locator: Sec. IV.B, Lindblad equation and local lowering operator
PDF page: 7
Claim: The source does not specify a reset channel, fixed post-reset state, or reset-state correctness invariant.
Gap scope: source_local

The local dissipator is part of continuous master-equation evolution, not a
discrete reset transaction.

## Missing Born branch history [literature_gap]
Fact ID: czarnik1811-gap-born-history
Source locator: Sec. IV.B, Lindblad equation and Fig. 6
PDF page: 7
Claim: The source does not provide Born branch masses, normalized conditional branches, ordered prefix masses, or a branch-completeness check.
Gap scope: source_local

The reported longitudinal magnetization is an ensemble expectation value.

## Missing complete Record law [literature_gap]
Fact ID: czarnik1811-gap-complete-record
Source locator: Sec. IV.B, Lindblad benchmark
PDF page: 7
Claim: The source does not define ordered raw outcomes, temporal detector folds, logical-observable folds, or a complete Record probability law.
Gap scope: source_local

No raw-to-Record map or Record-distance observable is present.

## Missing Clifford augmentation [literature_gap]
Fact ID: czarnik1811-gap-clifford-augmentation
Source locator: Sec. III.A and Fig. 1
PDF page: 3
Claim: The source represents the state or purification directly as an iPEPS and does not introduce a Clifford frame, stabilizer tableau, Pauli pull-through rule, or Clifford-augmented residual.
Gap scope: source_local

The ancilla gauge \(G(\beta)\) is a purification disentangler, not a Clifford
augmentation.

## Missing matched CAPEPS/full-PEPS resources [literature_gap]
Fact ID: czarnik1811-gap-matched-capeps-resources
Source locator: Appendix B, numerical-resource paragraph
PDF page: 12
Claim: The source does not report a matched-accuracy runtime, peak-memory, or throughput comparison between a Clifford-augmented PEPS method and full-PEPS evolution.
Gap scope: source_local

Its resource evidence compares only source-defined iPEPS update variants and
reports one full-update CPU workload.

## Missing executable provenance [literature_gap]
Fact ID: czarnik1811-gap-executable-provenance
Source locator: Appendix B, numerical details
PDF page: 12
Claim: The source supplies numerical settings and processor information but no implementation repository, version, commit, archived executable, or run artifact.
Gap scope: source_local

The paper is therefore reproducible only at the published algorithm and
parameter-description level.
