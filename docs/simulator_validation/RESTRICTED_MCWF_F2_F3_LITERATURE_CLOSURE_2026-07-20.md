# Restricted MCWF F2/F3 literature closure — 2026-07-20

## Frozen claim

`decision/consequence` — decide whether source evidence is sufficient to preregister, but not yet
implement, two additional two-qubit neutral fixtures and an independent dense Record oracle. A closed
packet authorizes only preregistration of F2 pure dephasing and F3 finite-temperature down/up
relaxation.

`mechanism` — Markovian Lindblad evolution with (F2)
`L_phi=sqrt(2 gamma_phi)|1><1|` and (F3)
`gamma(n_bar+1)D[sigma_-]+gamma n_bar D[sigma_+]`.

`observable/record object` — the schedule-ordered four-bit `[X,Z,X,Z]` selective-measurement law,
including the two declared reset operations, its two mechanism-directed binary marginals, and total
variation over fixed finite supports.

`mechanism→observable bridge` — Lindblad evolution to an MCWF ensemble; unnormalized selective
maps `M_x(tau)=P_x tau P_x`; explicit fixed-state reset
`R_0(tau)=|0><0|Tr(tau)`; composition in schedule order; deterministic label-to-bit
marginalization for the two-level fixtures.

`predicted direction/scale` — F2 must distinguish a coherence factor `exp(-gamma_phi t)` from
`exp(-gamma_phi t/2)`. F3 must have positive excitation from a reset ground state and must recover
the sourced finite-temperature equilibrium. Exact fixture values and finite-sample bands belong in
the preregistration, not this closure packet.

`alternative formulations/invariants` — number-projector and Pauli-Z dephasing must agree after
coefficient conversion; generalized amplitude damping and down/up Lindblad evolution must agree at
channel level; a unit-modulus collapse phase must not change the dissipator; X/Z operations must not
be reordered unless the relevant sequential-independence condition is proved.

`possible no-go` — a fixture is killed if its registered law cannot distinguish the load-bearing
normalization/direction corruptions. Collapse phase is a no-go for use as a physical corruption.

`implementation target` — a neutral versioned JSON fixture family, an isolated QuTiP worker, a
from-scratch NumPy/SciPy worker using 4x4 density matrices and a 16x16 Liouvillian, a separate
project-binding gate, and a registry-derived 15-statistic comparison family.

## Authority and corpus binding

The project claim boundary remains owned by `docs/SIMULATOR.md`, `docs/METRICS.md`, and
`docs/FAITHFULNESS_PROTOCOL.md`. Source-only claims below come from primary PDFs reopened at their
exact locators. The current artifact-verified corpus contains 15 notes and 172 `paper_fact` records at
corpus SHA-256 `46ac26a1ced20c297bfa0dbb32773b7fb86be9e2727b688774de8dbc04f794b9`.

Load-bearing new notes:

- `docs/papers/reading_notes/oi_schirmer_pure_dephasing_1109.0954_source_review.md`
- `docs/papers/reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md`
- `docs/papers/reading_notes/garner_thermal_relaxation_2512.09189_source_review.md`
- `docs/papers/reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md`

The existing admitted Sander note supplies the generic Lindblad-to-MCWF ensemble bridge. The
separate project-fit reconstruction is hash-bound at
`docs/simulator_validation/RESTRICTED_MCWF_F2_F3_PROJECT_FIT_AUDIT_2026-07-20.md`.

## Coverage ledger

| load-bearing row | required object | local evidence queried | external search queried | source/reading note | source location | status | implication |
|---|---|---|---|---|---|---|---|
| F2 physical model | dissipator convention and coherence-rate normalization | RAG `pure dephasing coherence rate diagonal Lindblad`; KG `diagonal pure-dephasing rate` | pure-dephasing and normalization searches below | Oi--Schirmer; Arsenijevic--Bankovic; Garner | Oi Eqs. (1)–(4), (6)–(11), PDF pp. 2, 4–5; Arsenijevic Eqs. (48), (55)–(57), PDF pp. 12–13; Garner Eqs. (1)–(4), PDF p. 3 | closed | `D[sqrt(2 gamma_phi)n]=(gamma_phi/2)D[sigma_z]` gives coherence decay `exp(-gamma_phi t)`; dropping `sqrt(2)` halves that rate. |
| F3 physical model | finite-temperature lowering and raising with a declared coefficient convention | RAG `thermal down up Lindblad generator detailed balance equilibrium`; KG `finite-temperature relaxation generator` | thermal down/up and detailed-balance searches below | Arsenijevic--Bankovic; Garner | Arsenijevic Eq. (16), PDF p. 5 and Eq. (18), PDF p. 6; Garner Eqs. (1)–(2), PDF p. 3 | closed | Downward and upward generator coefficients are respectively `gamma(n_bar+1)` and `gamma n_bar`. |
| F3 equilibrium/scale | finite-temperature stationary population and rate ratio | same local query | same external search | Garner; Arsenijevic--Bankovic | Garner Eqs. (10), (15), PDF p. 3; Arsenijevic Eq. (17), PDF p. 5 | closed | `p1*=n_bar/(1+2n_bar)` and `gamma_up/gamma_down=n_bar/(n_bar+1)`. |
| Observable | selective outcome mass and conditional state | RAG `ordered selective measurement reset joint distribution`; KG `ordered projective outcome law` | sequential-measurement search below | Czajkowski--Grilo | Sec. 2.2, Eq. (1), PDF p. 5 | closed | The dense worker must retain unnormalized branch mass until its trace is accumulated. |
| Ordered Record bridge | order-sensitive joint probability | same local query | same external search | Czajkowski--Grilo | Sec. 3.1, Eq. (9), Property 8 and Eq. (10), PDF p. 7 | closed | The `[X,Z,X,Z]` schedule is part of fixture identity; an unordered observable is not a substitute. |
| Reset composition | explicit fixed-state reset channel following a selective outcome | same local query | reset-channel search below | Garner plus the selective-update source | Garner Sec. II.C, Eq. (22), PDF p. 5; Czajkowski--Grilo Eq. (1), PDF p. 5 | closed | Composing `M_x` with `R_0` is an explicit CPTP design operation, not an implicit solver convention. |
| Lindblad→MCWF | ensemble bridge for the declared Markovian generator | RAG thermal query returned `sander-mcwf-ensemble` | no new source required | Sander et al. admitted source review | Sec. II.B, Eqs. (12)–(13); App. A, Eq. (A6), PDF p. 4 | closed | MCWF histograms may be compared to the density-matrix law only in the declared small-step/large-sample convergence setting. |
| Standard statistic | joint and marginal TV with finite-sample confidence | `docs/METRICS.md`; current protocol implementation | empirical-L1 search below | binding metric/code; auxiliary pinned Weissman technical report | `docs/METRICS.md` entries for MCWF Record convergence; protocol `multinomial_tv_radius` and `two_sample_tv_comparison`; Weissman Thm. 2.1, PDF p. 4 | closed | TV is the registered statistic. Bonferroni allocation must be derived from registry cardinality. |
| Symmetry/no-go | collapse phase gauge | pure-dephasing RAG query | collapse-gauge search below | Oi--Schirmer | Methods, Eqs. (10)–(11), PDF p. 5 | closed | `D[e^(i theta)L]=D[L]`; sign/phase is forbidden as a physical kill mutation. |
| Independent implementation path | hand-built matrices, Liouvillian, projectors, reset maps | all queries above | all selected primary sources | all four new notes plus Sander | exact rows above | closed | No production compiler, compiled Carrier program, production operator builder, or production measurement/reset helper may enter the dense worker. |

The Weissman report is pinned at `docs/papers/weissman_2003_l1_deviation.pdf`, SHA-256
`1e0a3f2904f6cde09ec34b8e87f69abf681fa75388e889112e00fabe4266203d`. It is a technical
report without an arXiv identifier or verified DOI, so the current fail-closed note schema cannot
represent it honestly and it is not admitted to `CURRENT_CORPUS.toml`. It is auxiliary support only;
the load-bearing metric premise is the already binding `docs/METRICS.md` contract and its tested
implementation.

## Anomaly ledger

| contrary fact / ambiguity | source and exact location | affected object | implication | status/action |
|---|---|---|---|---|
| Dephasing papers place coefficients either inside or outside `D[L]`. | Oi Eqs. (3), (6)–(7); Garner Eqs. (1)–(2); Arsenijevic Eqs. (48), (56) | F2 normalization | Freeze generator coefficient and collapse amplitude separately; cross-check number-projector and Pauli-Z forms. | resolved |
| A collapse sign or global phase is physically invisible. | Oi Eqs. (10)–(11), PDF p. 5 | corruption design | Reject sign/phase as a verdict-driving mutation; retain it as an invariance control. | resolved |
| Ordered X/Z measurements do not generally define an order-independent joint observable. | Czajkowski--Grilo Eq. (9), Property 8, PDF p. 7 | Record identity | Bind the exact order, keys, targets, reset flags, and reset states into fixture identity. | resolved |
| Garner's reset appears in a channel decomposition, not as the complete ordered schedule. | Garner Eq. (22), PDF p. 5 | reset bridge | Compose the sourced reset channel explicitly after the sourced selective map; do not claim the paper studied this schedule. | resolved as explicit design composition |
| Garner 2025 and all four new arXiv artifacts are not calibration evidence. | source title pages and scopes | claim boundary | Treat rates as neutral-fixture parameters only. | bounded |
| The generic MCWF source does not prove finite-bond or full-QEC-Record accuracy. | Sander source review and existing record-faithfulness closure | downstream promotion | Keep finite-bond and complete-Record claims open and out of this build authorization. | bounded |

## External acquisition ledger

The repository AnySearch connector was not callable in the current tool registry. The user-authorized
internet-search backend was therefore used for routing, followed by direct acquisition and full-text
inspection of the primary source objects. Search snippets were not used as evidence.

| gap row | backend + domain | exact query + date | candidate + publication/version check | disposition |
|---|---|---|---|---|
| F2 model/gauge | web academic, arxiv.org | `site:arxiv.org pure dephasing Lindblad diagonal collapse coherence rate gauge invariance Oi Schirmer` — 2026-07-20 | Oi--Schirmer, arXiv:1109.0954; pinned v1; no correction/retraction banner observed | selected; full text inspected at Eqs. (1)–(11) |
| F2 competing convention | web academic, arxiv.org | `site:arxiv.org/abs/1606.01145 generalized amplitude damping phase damping Kraus master equation` — 2026-07-20 | Arsenijevic--Bankovic, arXiv:1606.01145; pinned v1; journal reference present; no correction/retraction banner observed | selected; phase and thermal equations close independent-convention rows |
| F3 mechanism/equilibrium/reset | web academic, arxiv.org | `site:arxiv.org/abs/2512.09189 thermal relaxation noise stabilizer simulation` — 2026-07-20 | Garner et al., arXiv:2512.09189; pinned v1 preprint; no correction/retraction banner observed | selected; full text inspected at Eqs. (1)–(4), (10), (15), (22) |
| F3 competing source | web academic, arxiv.org | `site:arxiv.org finite temperature amplitude damping master equation gamma n+1 sigma- gamma n sigma+ detailed balance` — 2026-07-20 | Arsenijevic--Bankovic plus unrelated thermal/open-system results | selected Arsenijevic; rejected candidates without the explicit one-qubit down/up coefficient row |
| ordered observable | web academic, arxiv.org | `site:arxiv.org sequential projective measurements ordered probability Tr A B A rho selective update` — 2026-07-20 | Czajkowski--Grilo, arXiv:2101.08313; pinned v2; no correction/retraction banner observed | selected; full text inspected at Eq. (1), Eq. (9), Property 8 |
| ordered observable identity | web academic, arxiv.org | `site:arxiv.org/abs/2101.08313 on-state commutativity measurements joint distributions outcomes` — 2026-07-20 | Czajkowski--Grilo, arXiv:2101.08313v2 | selected; confirms exact source/version identity |
| statistical bound | web general | `Weissman Ordentlich Seroussi Verdu Weinberger L1 deviation empirical distribution 2^a-2 PDF` — 2026-07-20 | HP Labs HPL-2003-97 (R.1), technical report; no verified DOI/arXiv identity | full text inspected and pinned as auxiliary; deliberately excluded from current corpus rather than assigned a false identifier |
| gauge no-go | web academic, arxiv.org | `site:arxiv.org Lindblad collapse operator global phase invariance dissipator` — 2026-07-20 | broad Lindblad results; Oi--Schirmer already supplies an exact admitted gauge row | no additional source selected after saturation |

## Operation replay and implementation path

For `n=diag(0,1)`, Oi's diagonal-rate formula gives

`Gamma_01 = (1/2)|sqrt(2 gamma_phi)-0|^2 = gamma_phi`.

Thus `L_phi=sqrt(2 gamma_phi)n` preserves populations and multiplies coherence by
`exp(-gamma_phi t)`. The independent form follows from
`D[sigma_z]=4D[n]`, hence `(gamma_phi/2)D[sigma_z]=D[sqrt(2 gamma_phi)n]`.

For F3, write `sigma_-=|0><1|`, `sigma_+=|1><0|` and

`L(rho)=gamma(n_bar+1)D[sigma_-](rho)+gamma n_bar D[sigma_+](rho)`.

Then

`d rho_11/dt=-gamma(n_bar+1)rho_11+gamma n_bar rho_00`,

with `rho_11*=n_bar/(1+2n_bar)`. This exposes the raising family from a reset ground
state and makes removal or exchange of the two directions observable.

The independent dense worker will vectorize 4x4 density matrices, hand-build the 16x16
Liouvillian from the declared 4x4 lifted operators, apply `scipy.linalg.expm(t L)`, then compose
hand-built projectors and reset superoperators while retaining unnormalized branch traces. A
closed-form factorized-law check is required in addition to the matrix-exponential route. External
QuTiP and project paths consume only the neutral fixture; production identities are checked in a
separate binding gate.

## Closure verdict

- `closure_status: closed`
- Closed rows: F2 generator/rate convention; F3 down/up generator, detailed balance, and equilibrium;
  selective and ordered measurements; explicit reset composition; Lindblad-to-MCWF bridge; registered
  joint/marginal TV; collapse-gauge no-go; independent equation-to-code route.
- Remaining gaps for this restricted decision: none.
- Load-bearing notes: the four new notes listed above plus the admitted Sander MCWF source review.
- Supported implementation path: neutral two-qubit F2/F3 fixtures, isolated QuTiP, independent
  NumPy/SciPy density/Liouvillian reconstruction, project binding, and registry-driven comparisons.
- Allowed downstream action: hand this packet to `preregister-claim` only.
- Explicitly not closed: complete QEC Record faithfulness, finite-bond accuracy, calibration,
  baseline/benchmark provenance, PEPS/FET non-degeneracy, aggregate acceptance, or release readiness.
