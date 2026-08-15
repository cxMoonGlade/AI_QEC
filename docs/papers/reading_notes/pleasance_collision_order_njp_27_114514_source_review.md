+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.1088/1367-2630/ae1b31"
source_version = "version-of-record"
source_uri = "https://doi.org/10.1088/1367-2630/ae1b31"
source_artifact = "docs/papers/NJP_27_114514_ae1b31_version_of_record.pdf"
source_sha256 = "81cc766164072cd022202357fec314684e8b0c28a2bfebd6132c1639af022426"
title = "Non-Markovianity in collision models with initial intra-environment correlations"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/PLEASANCE_NJP_AE1B31_COLLISION_ORDER_AUDIT_2026-08-01.md"
audit_packet_sha256 = "7640499c597fdbeafd1db8fdb4aa62d62d6154dd587a7b3cf1272914ae525b80"
admission_status = "source_only_reviewed"
admission_reviewer = "independent-source-only-admission-review-wf_8b4fc2de-2026-08-01"
admission_date = "2026-08-01"
visually_checked_pages = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 19]

[[relations]]
predicate = "defines"
object_id = "correlated-ancilla-collision-model"
object_type = "model"
object_label = "overlapping groups of L ancillas"
fact_id = "pleasance-model-definition"

[[relations]]
predicate = "derives"
object_id = "composite-cm-markovian-embedding"
object_type = "theorem"
object_label = "enlarged system"
fact_id = "pleasance-ccm-theorem"

[[relations]]
predicate = "derives"
object_id = "collision-order-markovianity"
object_type = "theorem"
object_label = "Markovian for all values of tau and epsilon"
fact_id = "pleasance-order-dependence"

[[relations]]
predicate = "limits"
object_id = "aa-entanglement-necessity"
object_type = "limitation"
object_label = "necessary although not sufficient"
fact_id = "pleasance-aa-entanglement-necessary"

[[relations]]
predicate = "derives"
object_id = "backflow-correlation-bound"
object_type = "theorem"
object_label = "total correlations between the system and the ancilla"
fact_id = "pleasance-backflow-bound"

[[relations]]
predicate = "derives"
object_id = "commuting-w-invariance"
object_type = "theorem"
object_label = "commutes with the system-ancilla interaction"
fact_id = "pleasance-commuting-w"

[[relations]]
predicate = "measures"
object_id = "blp-nonmarkovianity-phase-diagram"
object_type = "observable"
object_label = "interior maxima"
fact_id = "pleasance-phase-diagram"
+++
# Full-text review — Pleasance, Neira, Merkli, and Petruccione, "Non-Markovianity in collision models with initial intra-environment correlations"

## Source identity [paper_fact]
Fact ID: pleasance-source-identity
Source locator: Article header, publication history block, and DOI line
PDF page: 2
Claim: The reviewed fixed source is the open-access version of record New J. Phys. 27 114514 (2025), DOI 10.1088/1367-2630/ae1b31, received 17 July 2025 and published 13 November 2025, by Pleasance, Neira, Merkli, and Petruccione.

PDF pages cited in this note are artifact pages 1-21; the printed article page is
the artifact page minus one.

## Selection scope [paper_fact]
Fact ID: pleasance-selection-scope
Source locator: Abstract (PDF page 2) and Sec. 1 (PDF pages 2-3)
PDF page: 2
Claim: The source studies how ancilla-ancilla entanglement, generated operationally by correlating overlapping groups of ancillas before they collide with the system, controls the non-Markovianity of an open system in a collision model.

## Model definition [paper_fact]
Fact ID: pleasance-model-definition
Source locator: Sec. 3, Eqs. (4)-(7) (PDF pages 4-5) and figure 1 (PDF page 3)
PDF page: 4
Claim: The model applies a unitary (or CPTP) operation W to overlapping groups of L ancillas in sequence to build the initial environment state, then interleaves pairwise system-ancilla collisions U, giving the generally non-factorizable reduced map Lambda_n of Eq. (7), with L called the correlation length.

## Commuting-W invariance [paper_fact]
Fact ID: pleasance-commuting-w
Source locator: Remark and Eq. (8)
PDF page: 5
Claim: If the correlation-generating operation W commutes with the system-ancilla interaction U, the intra-environment correlations drop out of the reduced system dynamics entirely.

## Composite-CM theorem [paper_fact]
Fact ID: pleasance-ccm-theorem
Source locator: Sec. 3.1, Theorem 1, Eqs. (9)-(10) (PDF page 5); Proposition 1, Eq. (13) (PDF page 6); proof Sec. 6.1 (PDF page 14)
PDF page: 5
Claim: The reduced state after n collisions equals the partial trace of the n-th power of one CPTP map M acting on the enlarged system of S plus L-1 ancillas, an embedding whose dimension grows as dim(H_S) d^(L-1) and whose L-1 ancillas constitute the memory part of the environment.

The source distinguishes its map M from the Campbell et al. composite map M-prime
(Eq. (14)): the order of the entangling and collision operations differs, and in M
the system reaches the memory only through the non-memory part. Footnote 5 records
that the two papers' memory-depth conventions differ by one.

## All-qubit collision operators [paper_fact]
Fact ID: pleasance-collision-operators
Source locator: Sec. 4, Eq. (15) (PDF page 7) and Eq. (22) (PDF page 8)
PDF page: 7
Claim: The all-qubit analysis takes U_Sj = exp(-i tau sigma_x tensor sigma_x^(j)) and W_[j+1,j] = exp(-i epsilon sigma_z^(j+1) tensor sigma_z^(j)) with correlation length L = 2 and each ancilla initialized in |+><+|.

## BLP witness formulation [paper_fact]
Fact ID: pleasance-blp-formulation
Source locator: Sec. 4.2, Eqs. (23)-(25) (PDF page 8) and Eqs. (26)-(29) (PDF page 9)
PDF page: 9
Claim: Non-Markovianity is quantified by the BLP measure over positive trace-distance increments, and for this model the decoherence-function form of the trace distance (Eq. (26)) makes the positive-increment set independent of the initial state pair, so |D(n+1)| > |D(n)| is necessary and sufficient for non-Markovianity.

## Non-monotone phase diagram [paper_fact]
Fact ID: pleasance-phase-diagram
Source locator: Fig. 4 (PDF page 9), Fig. 5 and Eq. (30) (PDF page 10), Eq. (40) (PDF page 13)
PDF page: 9
Claim: The BLP measure over the phases (epsilon, tau) has interior maxima near epsilon = 0.195 pi and tau in {0.15 pi, 0.35 pi}, vanishes on the lines where epsilon or tau equals 0, pi/4, or pi/2, and at tau = pi/4 the dynamics is Markovian regardless of epsilon since D(n) = exp(-i pi n / 2) cos(2 epsilon) for n >= 1.

## AA entanglement necessary [paper_fact]
Fact ID: pleasance-aa-entanglement-necessary
Source locator: Eq. (33) with Fig. 6 discussion (PDF page 11); Conclusions (PDF page 13)
PDF page: 11
Claim: At epsilon = pi/4 the concurrence of every interacting ancilla pair beyond the first vanishes -- an elimination the source states may be interpreted as an effect of entanglement monogamy -- and D(n) = (cos 2 tau)^n is strictly nonincreasing, eliminating all non-Markovianity, and the conclusions state that ancilla-ancilla entanglement within the interacting portion is necessary although not sufficient for non-Markovian behavior.

## Order dependence [paper_fact]
Fact ID: pleasance-order-dependence
Source locator: Abstract (PDF page 2); Sec. 4.3, Eqs. (41)-(42) (PDF page 13); proof Sec. 6.5, Eqs. (91)-(95) (PDF page 19)
PDF page: 13
Claim: When consecutive ancillas are entangled after the first member of each pair collides with the system, the decoherence function is D-prime(n) = exp(-2 i tau)(cos 2 tau - i sin 2 tau cos 2 epsilon)^(n-1), whose modulus never increases, so the dynamics is Markovian for all values of tau and epsilon.

## Backflow correlation bound [paper_fact]
Fact ID: pleasance-backflow-bound
Source locator: Eq. (35) (PDF page 11) and Eqs. (36)-(39) (PDF page 12)
PDF page: 11
Claim: The trace-distance increase between collisions n and m is bounded above by the sum of the total correlations between the system and the ancilla A_n and the distinguishability of the two reduced ancilla states, all evaluated immediately before the n-th collision, so a nonmonotonic increase requires nonzero such correlations or distinguishability.

The bound cites Laine, Piilo, and Breuer, EPL 92 60010 (reference [63]).

## No deterministic-schedule or ladder treatment [literature_gap]
Fact ID: pleasance-no-ladder
Source locator: Complete source scope, PDF pages 2-21 (Secs. 1-6)
PDF page: 2
Claim: The source treats a fresh-ancilla stream with operationally generated initial correlations and does not treat a persistent finite memory register, a deterministic every-other-collision exchange schedule, stochastic event masks, or any tensor-network carrier.
Gap scope: source_local
