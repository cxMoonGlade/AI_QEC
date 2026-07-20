+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1109.0954"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1109.0954v1"
source_artifact = "docs/papers/1109.0954v1.pdf"
source_sha256 = "29fb809a2f661af434bda4197fb22f4e109c662282e52905e2f55e6b9eb06a8c"
title = "Fundamental Speed Limits on Quantum Coherence and Correlation Decay"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/RESTRICTED_MCWF_F2_F3_PROJECT_FIT_AUDIT_2026-07-20.md"
audit_packet_sha256 = "321c10a1f152fe1baa183f297f2cddd4e3dbefeb3178d4b6fff7027cafbeb763"
admission_status = "source_only_reviewed"
admission_reviewer = "source_only_second_pass_2026_07_20"
admission_date = "2026-07-20"
visually_checked_pages = [1, 2, 4, 5]

[[relations]]
predicate = "defines"
object_id = "diagonal-pure-dephasing-rate"
object_type = "model"
object_label = "diagonal pure-dephasing rate"
fact_id = "oi-diagonal-rate"

[[relations]]
predicate = "defines"
object_id = "lindblad-collapse-gauge"
object_type = "concept"
object_label = "collapse-operator gauge invariance"
fact_id = "oi-collapse-gauge"
+++
# Source review — Oi and Schirmer on Markovian pure dephasing

## Source identity [paper_fact]
Fact ID: oi-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is the six-page arXiv:1109.0954v1 manuscript by Daniel K. L. Oi and Sophie G. Schirmer on constraints among Markovian pure-dephasing rates.

The title page dates the manuscript July 13, 2021 while the pinned arXiv version line records the
v1 submission identifier. The analysis treats finite-dimensional Markovian dephasing.

## Diagonal dephasing rate [paper_fact]
Fact ID: oi-diagonal-rate
Source locator: Results, Eqs. (1)–(4)
PDF page: 2
Claim: A diagonal pure-dephasing rate is one half the summed squared diagonal entries minus their real cross product, and each coherence magnitude decays exponentially at that rate.

For real diagonal entries the rate reduces to one half the sum of squared entry differences. The
populations remain constant, while the off-diagonal density elements acquire the stated damping and
any declared frequency shift.

## Lindblad dissipator convention [paper_fact]
Fact ID: oi-dissipator-convention
Source locator: Methods, Eqs. (6)–(9)
PDF page: 4
Claim: The Lindblad dissipator is `D[V](rho)=V rho V^dagger-1/2(V^dagger V rho+rho V^dagger V)`, and diagonal Hamiltonian and collapse operators characterize pure dephasing in the chosen basis.

Equation (9) repeats the exponential matrix-element evolution obtained from this convention. The
source states that pure dephasing leaves every basis-state population stationary.

## Collapse gauge invariance [paper_fact]
Fact ID: oi-collapse-gauge
Source locator: Methods, Eqs. (10)–(11)
PDF page: 5
Claim: The summed dissipator has collapse-operator gauge invariance under unitary mixing, while adding an identity multiple to a collapse operator produces only the stated effective-Hamiltonian correction.

The unitary mixing includes multiplication of a single collapse operator by a unit-modulus scalar.
The source uses these invariances to construct a canonical diagonal set without changing the generated
dynamics.

## Scope limit [literature_gap]
Fact ID: oi-gap-measurement-record
Source locator: Results, Eqs. (1)–(4), and Methods, Eqs. (6)–(11)
PDF page: 5
Claim: The source does not define selective measurement, reset, trajectory sampling, or an ordered multi-time outcome distribution.
Gap scope: source_local

Its outputs are density-matrix populations, coherences, dephasing rates, frequency shifts, and
correlation-decay constraints.
