+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2512.09189"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2512.09189v1"
source_artifact = "docs/papers/2512.09189v1.pdf"
source_sha256 = "c1be4a05112b90c3ec250cca2ffbe8bfce06b0fc443e9fc9b2c6bf63a0cb88e4"
title = "Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction"
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
visually_checked_pages = [1, 3, 5]

[[relations]]
predicate = "defines"
object_id = "finite-temperature-relaxation-generator"
object_type = "model"
object_label = "finite-temperature relaxation generator"
fact_id = "garner-thermal-generator"

[[relations]]
predicate = "defines"
object_id = "thermal-equilibrium-population"
object_type = "observable"
object_label = "thermal equilibrium population"
fact_id = "garner-equilibrium-population"

[[relations]]
predicate = "defines"
object_id = "state-reset-channel"
object_type = "model"
object_label = "state-reset channel"
fact_id = "garner-reset-channel"
+++
# Source review — Garner et al. on thermal-relaxation channels

## Source identity [paper_fact]
Fact ID: garner-source-identity
Source locator: Title page and abstract
PDF page: 1
Claim: The source is the sixteen-page arXiv:2512.09189v1 preprint by Sean R. Garner and coauthors on thermal-relaxation channels and stabilizer-compatible decompositions.

The title page is dated December 11, 2025. The abstract distinguishes exact channel treatment from
Pauli-twirling approximations and includes a finite-temperature extension.

## Thermal generator [paper_fact]
Fact ID: garner-thermal-generator
Source locator: Sec. II.A, Eqs. (1)–(2)
PDF page: 3
Claim: The finite-temperature relaxation generator contains downward `gamma(n_bar+1)D[|0><1|]`, upward `gamma n_bar D[|1><0|]`, and pure-dephasing `(gamma_phi/2)D[sigma_z]` terms under one explicit dissipator convention.

The thermal occupation is `n_bar=(exp(hbar omega/(k_B T_b))-1)^-1`. The dissipator is written
with the jump term and both anticommutator contributions.

## Coherence times [paper_fact]
Fact ID: garner-coherence-times
Source locator: Sec. II.A, Eqs. (3)–(4)
PDF page: 3
Claim: At zero temperature the excited population decays with `T1`, the coherence decays with `T2`, and `1/T2=1/(2T1)+1/T_phi`.

The pure-dephasing time is the reciprocal of the extra dephasing rate. The resulting constraint is
`T2<=2T1` for the stated model.

## Equilibrium population [paper_fact]
Fact ID: garner-equilibrium-population
Source locator: Sec. II.A, Eqs. (10) and (15)
PDF page: 3
Claim: The thermal equilibrium population is `p_1=n_bar/(1+2n_bar)`, while the total population-relaxation rate is `gamma(2n_bar+1)`.

The generalized-amplitude-damping parameter is `1-exp(-tau/T1)`. At nonzero thermal occupation,
both ground-reset and excited-reset branches have nonzero weights.

## State reset channel [paper_fact]
Fact ID: garner-reset-channel
Source locator: Sec. II.C, Eq. (22)
PDF page: 5
Claim: The amplitude-damping decomposition includes a state-reset channel `R_|0>` that maps its branch to the state `|0>`.

The same section distinguishes this nonunitary channel from identity and Pauli-Z channels. Later
finite-temperature formulas include both `R_|0>` and `R_|1>` branches.

## Scope limit [literature_gap]
Fact ID: garner-gap-selective-record
Source locator: Full-text scope established by Secs. II–V and appendices
PDF page: 5
Claim: The source does not derive an ordered selective X/Z measurement law from a trajectory algorithm or provide a finite-bond trajectory guarantee.
Gap scope: source_local

The reset channels appear inside channel decompositions and circuit simulations, not as a general
derivation of arbitrary selective-measurement schedules.
