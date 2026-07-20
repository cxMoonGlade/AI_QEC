+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1606.01145"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1606.01145v1"
source_artifact = "docs/papers/1606.01145v1.pdf"
source_sha256 = "32e3d12077bef0b1e6eb84f2f85f5bc35fc1fce6b5f9a3e58c625cf902ee0694"
title = "Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/RESTRICTED_MCWF_F2_F3_PROJECT_FIT_AUDIT_2026-07-20.md"
audit_packet_sha256 = "321c10a1f152fe1baa183f297f2cddd4e3dbefeb3178d4b6fff7027cafbeb763"
admission_status = "source_only_reviewed"
admission_reviewer = "source_only_second_pass_2026_07_20"
admission_date = "2026-07-20"
visually_checked_pages = [1, 5, 6, 12, 13]

[[relations]]
predicate = "defines"
object_id = "thermal-down-up-lindblad-generator"
object_type = "model"
object_label = "thermal down/up Lindblad generator"
fact_id = "arsenijevic-thermal-generator"

[[relations]]
predicate = "derives"
object_id = "generalized-amplitude-damping-channel"
object_type = "model"
object_label = "generalized amplitude-damping channel"
fact_id = "arsenijevic-gad-channel"

[[relations]]
predicate = "defines"
object_id = "phase-damping-channel"
object_type = "model"
object_label = "phase-damping channel"
fact_id = "arsenijevic-phase-damping"
+++
# Source review — Arsenijevic and Bankovic on amplitude and phase damping

## Source identity [paper_fact]
Fact ID: arsenijevic-source-identity
Source locator: Title page and abstract
PDF page: 1
Claim: The source is the arXiv:1606.01145v1 manuscript by Momir Arsenijevic and Nevena Bankovic deriving one-qubit generalized amplitude-damping and phase-damping Kraus operators from master equations.

The pinned artifact contains fifteen PDF pages and identifies a journal appearance in Kragujevac
Journal of Science volume 38.

## Thermal down and up generator [paper_fact]
Fact ID: arsenijevic-thermal-generator
Source locator: Sec. 3, Eq. (16)
PDF page: 5
Claim: The microscopic thermal master equation contains a thermal down/up Lindblad generator with downward coefficient `2 pi J(omega_0)(n_bar+1)` and upward coefficient `2 pi J(omega_0)n_bar`.

The lowering term contains `sigma_- rho sigma_+` and the anticommutator of `sigma_+ sigma_-`;
the raising term contains `sigma_+ rho sigma_-` and the anticommutator of `sigma_- sigma_+`.
The upward coefficient vanishes at zero temperature.

## Generalized amplitude damping [paper_fact]
Fact ID: arsenijevic-gad-channel
Source locator: Sec. 3, Eqs. (17)–(18)
PDF page: 5
Claim: The finite-temperature master equation generates a generalized amplitude-damping channel with four Kraus branches and distinct positive downward and upward rates.

The relaxation parameter depends on the thermal occupation through `2N_th+1`. The accompanying
parameter weights the asymptotic thermal populations, and the text states that the equation reduces
to standard amplitude damping at zero temperature.

## Explicit down/up decomposition [paper_fact]
Fact ID: arsenijevic-down-up-decomposition
Source locator: Sec. 3, Eq. (18)
PDF page: 6
Claim: The interaction-picture generator separates into a lowering dissipator with coefficient `y` and a raising dissipator with coefficient `z`, with `y>z>=0` under the declared thermal model.

The Hamiltonian term is written separately. This form makes the two directional dissipators and
their normalizations explicit.

## Phase damping [paper_fact]
Fact ID: arsenijevic-phase-damping
Source locator: Sec. 4, Eqs. (48)–(49)
PDF page: 12
Claim: The phase-damping channel obeys `d rho/dt=r(sigma_z rho sigma_z-rho)` and is derived as pure decoherence without energy loss.

The rate is related to the low-frequency spectral density and thermal occupation under the source's
stated limiting assumptions.

## Phase-damping solution [paper_fact]
Fact ID: arsenijevic-phase-solution
Source locator: Sec. 4, Eqs. (55)–(57)
PDF page: 13
Claim: The phase-damping solution preserves the `sigma_z` component and multiplies the `sigma_x` and `sigma_y` components by `exp(-2rt)`.

The two displayed Kraus forms satisfy completeness and generate the same Bloch-component evolution.

## Scope limit [literature_gap]
Fact ID: arsenijevic-gap-trajectory-record
Source locator: Full-text scope established by Secs. 2–5
PDF page: 13
Claim: The source does not define stochastic trajectory sampling, ordered selective measurements, reset composition, or finite-sample distribution comparison.
Gap scope: source_local

The analysis connects local master equations to finite-time Kraus maps and Bloch-sphere evolution.
