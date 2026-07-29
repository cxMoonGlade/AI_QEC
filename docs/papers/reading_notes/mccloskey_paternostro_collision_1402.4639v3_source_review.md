+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1402.4639"
source_version = "v3"
source_uri = "https://arxiv.org/abs/1402.4639v3"
source_artifact = "docs/papers/1402.4639v3.pdf"
source_sha256 = "eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc"
title = "Non-Markovianity and System-Environment Correlations in a Microscopic Collision Model"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/MCCLOSKEY_PATERNOSTRO_1402_4639V3_COLLISION_AUDIT_2026-07-29.md"
audit_packet_sha256 = "4b28940ef532ff180f1e83a558ab5db3bee8de142b8283e17117712bb548577e"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-rereview-blp-mccloskey-round3-2026-07-29"
admission_date = "2026-07-29"
visually_checked_pages = [1, 2, 3, 4, 5, 6]

[[relations]]
predicate = "defines"
object_id = "partial-swap-collision"
object_type = "model"
object_label = "partial-SWAP unitary"
fact_id = "mp-system-collision"

[[relations]]
predicate = "supports"
object_id = "retained-system-environment-correlations"
object_type = "concept"
object_label = "retains the system-environment correlations"
fact_id = "mp-strategy-two"

+++
# Full-text review — McCloskey and Paternostro, “Non-Markovianity and System-Environment Correlations in a Microscopic Collision Model”

## Source identity [paper_fact]
Fact ID: mp-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The reviewed fixed source is the seven-page preprint arXiv:1402.4639v3 by McCloskey and Paternostro.

The artifact visibly carries the arXiv version line `26 May 2014` and the
title-page line `Dated: November 27, 2021`. This source-only record preserves
both visible dates without explaining their discrepancy.

## Selection scope [paper_fact]
Fact ID: mp-selection-scope
Source locator: Abstract and Sec. I opening
PDF page: 1
Claim: The source studies how retaining or erasing system-environment correlations changes trace-distance non-Markovianity in an iterative qubit collision model.

## System–ancilla collision [paper_fact]
Fact ID: mp-system-collision
Source locator: Sec. I, Eqs. (1)–(2)
PDF page: 2
Claim: The source models a system–ancilla collision by the partial-SWAP unitary \(\widehat U_{S,j}(\gamma)=\cos\gamma\,I+i\sin\gamma\,\widehat S_{S,j}\).

Equation (2) prints the four-by-four SWAP matrix in the ordered computational
basis.

## Ancilla–ancilla collision [paper_fact]
Fact ID: mp-environment-collision
Source locator: Sec. I, Eqs. (3)–(4)
PDF page: 2
Claim: Adjacent environment qubits interact through a second partial-SWAP unitary with strength \(\delta\), allowing information from one collision to be carried to a later ancilla.

## Joint and reduced evolution [paper_fact]
Fact ID: mp-joint-reduced-evolution
Source locator: Sec. I, Eq. (5) and following paragraph
PDF page: 2
Claim: The source obtains the joint state after \(n\) collisions by one overall unitary and obtains system dynamics by discarding environment degrees of freedom.

## Trace-distance observable [paper_fact]
Fact ID: mp-trace-distance
Source locator: Sec. I, Eqs. (6)–(7)
PDF page: 3
Claim: The source uses trace distance and the positive-time portion of its derivative to define its non-Markovianity observable.

## Printed prior-pair argument defect [literature_gap]
Fact ID: mp-gap-equation-eight-self-distance
Source locator: Sec. I, Eq. (8)
PDF page: 3
Claim: The source supplies no literally usable prior-pair term in Eq. (8), because its printed second distance compares \(\rho^S_{2,n-1}\) with itself and is identically zero.
Gap scope: source_local

The printed term is
\(D(\rho^S_{2,n-1},\rho^S_{2,n-1})\), rather than the distance between the
two trajectories at step \(n-1\).

## Missing positive-increment selector [literature_gap]
Fact ID: mp-gap-equation-eight-positive-selector
Source locator: Sec. I, Eqs. (7)–(8)
PDF page: 3
Claim: The source supplies no literally usable discrete positive-growth formula because Eq. (8) prints an unrestricted sum without the positive-increment restriction imposed by Eq. (7).
Gap scope: source_local

Correcting only the two prior-state arguments would make the unrestricted sum
telescope; it would not sum total positive growth.

## Correlation-erasing strategy [paper_fact]
Fact ID: mp-strategy-one
Source locator: Sec. I.B, Eq. (10) and surrounding definition of Strategy 1
PDF page: 4
Claim: Strategy 1 traces an ancilla early enough to erase its correlation with the system before that correlation can affect the next system collision.

## Correlation-retaining strategy [paper_fact]
Fact ID: mp-strategy-two
Source locator: Sec. I.B, Eq. (11) and following comparison
PDF page: 4
Claim: Strategy 2 retains the system-environment correlations through the ancilla's interaction with its next neighbor and erases an ancilla only after its active role expires.

## Retention-dependent threshold [paper_fact]
Fact ID: mp-retention-threshold
Source locator: Fig. 4 and Sec. II.A
PDF page: 5
Claim: For the displayed parameters, Strategy 2 has a lower threshold in the intra-environment interaction strength \(\delta\) above which the optimized non-Markovianity measure is nonzero than Strategy 1.

## Non-Markovianity under both strategies [paper_fact]
Fact ID: mp-both-strategies-nonmarkovian
Source locator: Sec. II.A, paragraphs following Fig. 3
PDF page: 5
Claim: The source reports that the dynamics can remain non-Markovian under both correlation-erasing Strategy 1 and correlation-retaining Strategy 2.

## Interaction-strength dependence [paper_fact]
Fact ID: mp-interaction-strength-dependence
Source locator: Figs. 3–4 and Sec. II.A
PDF page: 5
Claim: At the displayed fixed system-environment strength \(\gamma=0.05\), the source reports that the degree and qualitative features of non-Markovianity depend on the intra-environment strength \(\delta\).

Figure 3 compares \(\delta=\pi/2\) with
\(\delta=0.95\times\pi/2\). Figure 4 scans 100 values of
\(\delta\in[0,\pi/2]\), with \(\gamma=0.05\) fixed.

## Initial-preparation dependence [paper_fact]
Fact ID: mp-initial-preparation-dependence
Source locator: Sec. II.A, paragraphs following Fig. 4
PDF page: 5
Claim: The source reports different optimizing initial-system state pairs for Strategies 1 and 2, so the quantitative non-Markovianity result depends on initial preparation.

## Stochastic collision draw-and-threshold rule [paper_fact]
Fact ID: mp-stochastic-collision-rule
Source locator: Sec. II.B and Fig. 6
PDF page: 6
Claim: The source draws a random variable at each step and executes the system-environment collision only when the draw lies below a threshold in \([0,1]\).

## Full-swap stochastic finding [paper_fact]
Fact ID: mp-stochastic-full-swap-finding
Source locator: Sec. II.B and Fig. 6
PDF page: 6
Claim: For the displayed full ancilla-swap case \(\delta=\pi/2\), reducing system-environment collision occurrence changes the period of trace-distance oscillations while leaving their amplitude unaffected.

## Unspecified random-variable distribution [literature_gap]
Fact ID: mp-gap-stochastic-draw-distribution
Source locator: Sec. II.B, random-variable paragraph
PDF page: 6
Claim: The source does not specify the random variable's distribution and therefore does not establish that the threshold numerically equals a Bernoulli collision probability.
Gap scope: source_local

## Unsupported monotonic-entanglement implication [literature_gap]
Fact ID: mp-gap-monotonic-entanglement
Source locator: Complete-text review, pages 1–7
PDF page: 1
Claim: The source does not establish monotonic entanglement growth with collision count.
Gap scope: source_local

## Unsupported PEPS-bond implication [literature_gap]
Fact ID: mp-gap-peps-bond
Source locator: Complete-text review, pages 1–7
PDF page: 1
Claim: The source does not define or bound a PEPS virtual-bond dimension.
Gap scope: source_local

## Unsupported truncation-error implication [literature_gap]
Fact ID: mp-gap-truncation-error
Source locator: Complete-text review, pages 1–7
PDF page: 1
Claim: The source does not define a tensor-network truncation error.
Gap scope: source_local

## Unsupported runtime implication [literature_gap]
Fact ID: mp-gap-runtime
Source locator: Complete-text review, pages 1–7
PDF page: 1
Claim: The source does not establish an algorithmic runtime metric.
Gap scope: source_local
