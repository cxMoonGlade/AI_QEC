# Finite-RTN free-induction diagnostic — clean-room literature closure (2026-07-15)

This packet decides whether a narrow diagnostic attached to the current source process can be
retained during retired-product cleanup. It is not a preregistration and does not promote the
diagnostic to a production-channel claim.

## Frozen claim

| field | frozen value |
|---|---|
| decision/consequence | retain or delete the finite-RTN diagnostic script and test |
| mechanism | independent stationary symmetric two-state CTMCs, used only through two explicitly declared one-qubit longitudinal free-induction lifts |
| observable/record object | exact coherence magnitude and positive trace-distance excursion for an equatorial state pair; no syndrome record |
| mechanism-to-observable bridge | Bergli exact RTN free-induction coherence; independence product; for pure dephasing the equatorial-pair trace distance equals the coherence magnitude |
| predicted direction/scale | current design defaults are tested numerically for a positive excursion over the declared finite horizon; the literature does not predict those repository-specific values |
| alternatives/invariants | full joint-state Feynman–Kac oracle, cycle-held transfer oracle, Gaussian weak-noise control, all-weak control, rate-convention and omitted-factor corruptions |
| possible no-go | an endpoint source alone has no quantum-map divisibility status; neither diagnostic is the production source fan-out, QEC channel, measurement record, or estimator |
| implementation target | current source owner `src/error_coupling_simulator/source/process.py`; repository research diagnostic and fresh-process acceptance test |

## Coverage ledger

| load-bearing row | required object | local evidence queried | external search queried | source/reading note | source location | status | implication |
|---|---|---|---|---|---|---|---|
| mechanism/rate convention | symmetric directional switching rate and endpoint autocorrelation | concept index, source implementation, primary PDF | not needed after primary closure | [Bergli–Galperin–Altshuler RTN reading note](../papers/reading_notes/bergli_galperin_altshuler_rtn_0904.4597.md) | Bergli Sec. 3.1, Eq. (15), PDF p. 7 | closed | use `exp(-2 gamma t)` and `p_flip=(1-exp(-2 gamma))/2` |
| exact single-mode coherence | non-Gaussian longitudinal free-induction factor | primary PDF and clean note | not needed after primary closure | same note | Bergli Eqs. (32)–(35), PDF pp. 9–10 | closed | exact weak/strong/equality branches are implementable |
| independent product | characteristic-function factorization | primary PDF and clean note | not needed after primary closure | same note | Bergli text before Eq. (39), PDF p. 13 | closed | multiply only for an explicitly independent finite set |
| observable and witness | trace-distance growth and positive-excursion sum | primary PDF and clean note | not needed after primary closure | [Breuer–Laine–Piilo non-Markovianity reading note](../papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md) | BLP Eqs. (1), (5), (9)–(12), PDF pp. 1–3 | closed | any positive excursion for one pair witnesses non-divisibility of that named map family |
| pure-dephasing bridge | equatorial-pair distance equals coherence magnitude | primary PDF plus transparent qubit algebra | not needed after primary closure | BLP clean note | BLP Eq. (14) and following text, PDF p. 4 | closed | `D(t)=|L(t)|` for the declared equatorial pair |
| repository default magnitude | numerical substitution into current design defaults | current source plus independent numerical oracles | not a literature premise | current diagnostic contract | project calculation | closed as project calculation | must be rerun against current source; not hardware calibration |
| production source-to-channel/record bridge | actual multi-parameter fan-out, schedule, measurement/reset, and record law | old local retrieval and current source boundary | no claim authorized | none | none | missing and excluded | no production CP-divisibility, record-memory, or estimator conclusion |
| implementation from equations | two analytic/factorized implementations plus different full-state oracles | current script/test audit | not a literature premise | current diagnostic contract | operation replay below | closed | retain under a neutral research-diagnostic name |

The removed package-local RAG command is unavailable by design (`ModuleNotFoundError` for the
retired namespace). The old KG returned no concept match. These surfaces were discovery-only and
closed no row. The current concept index routed directly to the two primary full-text objects above.

## Anomaly ledger

| contrary fact or ambiguity | source and exact location | affected object | implication | status/action |
|---|---|---|---|---|
| Gaussian covariance is insufficient for strong RTN | Bergli Secs. 3.2 and 6; Eqs. (35)–(38) | Gaussian control | keep only as a negative control, not ground truth | closed boundary |
| endpoint samples do not select a unique intra-cycle path | not supplied by either primary paper | source-to-lift bridge | continuous and held lifts must remain separately declared choices | explicit project choice |
| absence of sampled backflow is not a general divisibility proof | BLP implication is one-way, Eqs. (5), (9)–(12) | null interpretation | use `NULL_WITHIN_HORIZON`, never “proved divisible” | closed boundary |
| first historical result was inspected before a committed preregistration | pre-cleanup result record | evidence class | current document must be a post-result diagnostic contract, not a rewritten preregistration | enforced |
| production bridge is absent | source/process inspection and no primary bridge | production claim | stop propagation at the declared free-induction maps | open/excluded |

## External acquisition ledger

No external search was required in this cleanup pass. All load-bearing rows of the narrowly frozen
diagnostic were closed by locally cached primary full texts that were re-read and visually checked.
The unsupported production bridge is outside the retained claim rather than relabelled a literature
fact or a confirmed field-wide gap.

## Operation replay

| input | transformation | assumption | output | source | status |
|---|---|---|---|---|---|
| directional rate `gamma` | sum Poisson switch parity | stationary symmetric CTMC | `C(t)=exp(-2 gamma t)` | Bergli Eq. (15) | matched |
| `v`, `gamma`, `t` | solve telegraph ODE | longitudinal free induction, unbiased initial state | exact `L_k(t)` | Bergli Eqs. (34)–(35) | matched |
| `K` modes | multiply characteristic functions | statistical independence | `L(t)=product_k L_k(t)` | Bergli before Eq. (39) | matched |
| pure-dephasing `L(t)` | choose antipodal equatorial pair | same named map for both states | `D(t)=|L(t)|` | BLP Eq. (14) plus qubit algebra | matched |
| positive interval of `D` | sum endpoint increases | fixed pair and declared horizon | BLP lower-bound/witness | BLP Eqs. (10)–(12) | matched |
| endpoint source | infer production fan-out/channel/record | no bridge | production verdict | no source | unsupported; propagation stopped |

## Closure verdict

- `closure_status: closed` for the two explicitly named one-qubit free-induction diagnostics.
- Closed rows: rate convention, exact coherence, independent product, BLP witness, pure-dephasing
  observable bridge, and implementation path.
- Remaining gap: production source-to-channel-to-record bridge; it is outside the retained claim and
  remains explicitly `missing`.
- Load-bearing notes:
  - [Bergli–Galperin–Altshuler RTN reading note](../papers/reading_notes/bergli_galperin_altshuler_rtn_0904.4597.md)
  - [Breuer–Laine–Piilo non-Markovianity reading note](../papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md)
- Supported implementation path: neutral research diagnostic, independent full-state oracles,
  corruption controls, current source-owner acceptance, and no compatibility reader.
- Allowed downstream action: migrate and rerun the diagnostic under the current source owner. Do not
  claim a production QEC or record-memory result.
