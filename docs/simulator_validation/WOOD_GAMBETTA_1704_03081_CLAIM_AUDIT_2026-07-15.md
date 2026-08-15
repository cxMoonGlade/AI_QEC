# Wood--Gambetta leakage-definition claim audit -- 2026-07-15

Status: APS Version of Record (VOR) and its appendices read in full; load-bearing equations
visually checked. The earlier arXiv-v1 note failed two independent-review rounds and was not
admitted. The final VOR-pinned replacement records the publication formulas and all currently
load-bearing source conflicts; two independent fourth-round source-only reviews passed it. This packet contains project
application and must never be indexed as a literature fact. The first VOR admission review failed
because it found two additional load-bearing print conflicts. A second review passed that revision,
but a separate adversarial formula scan then exposed further load-bearing proof conflicts; the PASS
was therefore superseded before admission. A third review caught an imprecise "diagonal input"
description plus two more source conflicts. The expanded note is pending a fourth review.

## Frozen question

- **Decision / consequence:** decide which objects in the current qutrit-leakage owner may be
  attributed to Wood and Gambetta, and which must be described as current simulator design.
- **Mechanism:** a CPTP map on a direct sum of computational and leakage subspaces; the paper's
  examples include a two-level exchange Hamiltonian, a two-jump dissipative model, and a general
  Lindblad envelope.
- **Observable:** leakage rate `L1`, seepage rate `L2`, state coherence of leakage `C_L`, and the
  distinct channel-averaged coherent rates `C_L1` and `C_L2`.
- **Mechanism-to-observable bridge:** projector traces for `L1/L2`; the trace norm of the
  cross-subspace block for state `C_L`; Haar averages of that state quantity for `C_L1/C_L2`.
- **Direction / scale:** the exact formulas in VOR Eqs. (59)--(61) apply to the paper's pure
  exchange unitary; no source-defined scale is assumed for the current simulator.
- **Alternative / invariant:** `d1 L1 = d2 L2` for unital maps; DLE/DLM retain `L1/L2` while
  discarding coherent leakage.
- **Possible no-go:** `L1 + L2` is not a coherence measure, and the simple LRB decay requires
  sufficient depolarization of the leakage subspace.
- **Implementation target:**
  `src/error_coupling_simulator/mechanisms/qutrit_leakage.py` and its current callers, schemas,
  tests, and authority documentation.

## Source object and clean-room search log

Current evidence object:

- Christopher J. Wood and Jay M. Gambetta, *Quantification and Characterization of Leakage
  Errors*, *Physical Review A* **97**, 032306 (2018);
- source identity: `doi:10.1103/PhysRevA.97.032306`, `version-of-record`;
- DOI URI: `https://doi.org/10.1103/PhysRevA.97.032306`;
- official APS full text:
  `https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevA.97.032306/fulltext`;
- local source:
  `docs/papers/wood_gambetta_leakage_characterization_pra_97_032306.pdf`;
- SHA-256: `66a9d749cdb5841b3cc565debc33bd17fcb46946c13d374ccd274fc87234169b`;
- page count: 17, including Appendices A--E;
- VOR dates: received 2017-05-17, published 2018-03-08.

Comparison object retained only as an original-source cache:

- arXiv `1704.03081v1`, submitted 2017-04-10;
- `docs/papers/wood_gambetta_leakage_characterization_1704.03081.pdf`;
- SHA-256: `789f605107a2e0e4203ce65fe3cbbe6934efda7d675f0e3d7a893278ac03bdfb`;
- 19 pages. The VOR, not this preprint, is the current literature-note authority.

Official metadata checked 2026-07-15: arXiv exposes only v1; Crossmark reports the document
current and lists no correction, erratum, or retraction; APS, arXiv, and IBM expose no separate
supplement, code, or dataset. This is an official-record statement, not proof that no code was ever
posted elsewhere.

The current manifest was queried first with
`leakage seepage average gate fidelity unitarity Wood Gambetta`. Both neutral retrieval tools
correctly refused retrieval because `docs/papers/CURRENT_CORPUS.toml` was bootstrap-empty. No old
mixed note or cache was read. The VOR was then obtained from the official APS full-text endpoint,
extracted with `pypdf`, read across all 17 pages, and visually checked on PDF pp. 1--16.

## VOR versus arXiv-v1 comparison

| item | VOR result | audit consequence |
|---|---|---|
| v1 Eqs. (39)--(40) channel coherent-rate inputs | fixed in VOR Eqs. (42)--(43), PDF p. 7: diagonal inputs `|psi_1><psi_1|` and `|psi_2><psi_2|` | delete the v1-only definition conflict; fixed-state current code still does not implement either Haar average |
| Appendix C Eq. (C1) | consistent with VOR Eqs. (42)--(43) | no longer a conflict |
| Appendix C Eqs. (C5)--(C6) | still switch from `1_1` to `1_2 tensor 1_2`, PDF p. 15 | retain source-conflict warning |
| Appendix C Eq. (C11) | still prints equality after an upper-bound chain, PDF p. 16 | retain source-conflict warning |
| v1 Eq. (47) twirl | edited as VOR Eq. (49), but `U_2,V_2` remain under a double-index sum with only one `|P_2|` normalization, PDF p. 8 | twirl cannot be uniquely replayed; preserve Eqs. (53)--(55) only as stated diagnostics |
| v1 Eq. (56) propagator | VOR Eq. (58) still omits `-i` from the sine cross term, PDF p. 9 | replay the defining exponential, never the inconsistent expansion |
| Appendix A cross terms | VOR Eq. (A16) repeats `D_1 E D_2` and omits `D_2 E D_1`, while Eq. (A17) and main-text Eq. (50) contain both directions, PDF p. 14 | do not use Eq. (A16) as an independent exact oracle |
| Lindblad dissipator | VOR Eq. (70) leaves the anticommutator's `k` outside the explicit sum and without `gamma_k`, unlike Eqs. (26)--(27) and Appendix E, PDF p. 10 | use the source's explicit `gamma D[A]` convention for replay and preserve Eq. (70) as conflicted printing |
| Appendix D adjoint action | the line after Eq. (D2) prints `L1 beta +(1-L2) beta`, but Eq. (D3) requires `L2 alpha +(1-L2) beta`, PDF p. 16 | Lemma 1's matrix path remains distinguishable from the inconsistent displayed line |
| Appendix D adjoint normalization | Eq. (D2) swaps normalized `D_ij` maps under adjoint without the required `d_j/d_i` factors from Eq. (47)/Eq. (A18), PDF p. 16 | Eq. (D3) follows the correctly normalized projector action; Eq. (D2) is not a valid general adjoint identity |
| Appendix C SWAP basis | Eqs. (C9)--(C10) omit conjugation/adjoint after specifying only an orthonormal operator basis, PDF p. 15 | displayed identity needs a Hermitian or self-dual basis choice not stated in the proof |
| Appendix E ladder sum | Eq. (E2) permits multiple `alpha_s`, but Eq. (E3) collapses the projected product to one term "for some s", PDF p. 16 | realness can be recovered termwise; the printed equality does not prove the full stated operator class |
| operator-basis cardinality | Appendix A indexes an `L(X1)` basis only through `d1-1`, and Appendix C uses the same upper limit in SWAP sums, although the space has dimension `d1^2`, PDFs pp. 14--15 | the source's own qubit `{I,X,Y,Z}` example contradicts its printed range |
| Appendix D iteration symbol | Eq. (D1) iterates undefined `E_m` adjoint, while Eq. (D2) defines the needed `E_L` adjoint, PDF p. 16 | preserve the subscript error; later algebra is read as the DLE adjoint chain |
| v1 Eqs. (58)--(59), (67)--(72), Lemma 2 | renumbered but materially retained in VOR Eqs. (60)--(61), (69)--(74), Lemma 2 | all provenance below uses VOR section, equation, and PDF-page coordinates |
| LRB assumptions | VOR main text has two physical assumptions; Appendix A has Assumptions 1--3 | do not reuse the v1 assumption numbering |

Additional VOR defects observed by the adversarial scan but not used by the present attribution
decision are retained here for the later all-formula audit: Eq. (41) divides by transition
probabilities without defining zero-rate boundary blocks; Eqs. (56) and (A24) use undefined `p1`
where Eq. (A20) indicates `L1`; Appendix A uses undefined `U_j` before Eq. (A1), omits `i` from a
purported one-dimensional phase after Eq. (A15), invokes Hilbert--Schmidt orthogonality where
zero cross-products are the needed argument, and labels a squared deterministic bias
`epsilon_Q^2` as variance. These observations are not admitted as RAG facts in this bounded note,
and this list is not claimed exhaustive.

## Notation ledger

| symbol | paper meaning | domain / condition | VOR location |
|---|---|---|---|
| `X = X1 direct-sum X2` | full state space split into computational and leakage subspaces | dimensions `d1`, `d2` | Sec. II, PDF p. 2 |
| `1_1`, `1_2` | orthogonal projectors onto `X1`, `X2` | `1_1 + 1_2 = 1` | Eqs. (1)--(2), PDF p. 2 |
| `L(rho)` | leaked population `Tr[1_2 rho]` | density operator on `X` | Eq. (1), PDF p. 2 |
| `L1(E)`, `L2(E)` | average leakage from `X1` and seepage from `X2` | arbitrary CPTP map `E` | Eq. (2), PDF p. 2 |
| `P_I`, `P_C` | incoherent block projection and complementary cross-block projection | superoperators on operators over `X` | Eqs. (30)--(33), PDF p. 6 |
| `C_L(rho)` | trace norm of the cross-subspace block of one state | state observable, not a channel average | Eq. (34), PDF p. 6 |
| `C_L1(E)`, `C_L2(E)` | Haar averages of state `C_L` after rank-one projectors from all pure states in `X1`, `X2` | channel-level coherent rates | Eqs. (42)--(43), PDF p. 7 |
| `U(t)` | defined as `exp(-itH)` for `H=(|1><2|+|2><1|)/2` | printed expansion omits `-i` from sine term | Eqs. (57)--(58), PDF p. 9 |
| `mathcal H`, `mathcal D` | unitary and dissipative Lindblad superoperator generators; `H` remains the Hamiltonian operator | Eq. (70)'s printed dissipator has a sum/rate-scope conflict | Eqs. (69)--(70), PDF p. 10 |
| `A21`, `A12` | leakage and seepage ladder operators | pure dissipative example with rates `gamma1`, `gamma2` | Eqs. (72)--(74), PDF p. 11 |

## Operation replay

The source was closed before the following reconstruction. The replay used only hand-typed NumPy
and SciPy algebra; it did not import a simulator package.

| input | transformation | assumption | output | exact VOR location |
|---|---|---|---|---|
| `E`, `1_1`, `1_2`, `d1`, `d2` | evaluate `Tr[1_2 E(1_1)]/d1` and `Tr[1_1 E(1_2)]/d2` | `E` is CPTP; direct-sum split fixed | Eq. (2) leakage and seepage rates | Sec. II, Eq. (2), PDF p. 2 |
| `rho` | form `1_1 rho 1_2 + 1_2 rho 1_1`, then sum singular values | trace norm is the chosen norm | state `C_L(rho)` | Sec. V.A, Eqs. (33)--(34), PDF p. 6 |
| pure-state inputs in `X_j` | evaluate state `C_L` after `E`, then Haar-average rank-one projectors within each subspace | all Haar-distributed pure states, not a fixed-basis diagonal set | channel `C_L1/C_L2` definitions | Sec. V.B, Eqs. (42)--(43), PDF p. 7 |
| printed DLM twirl | compare sum indices and normalization in Eq. (49) | no unstated correlation between `U_2,V_2` | operation cannot be uniquely normalized from the VOR | Sec. VI.A.3, Eq. (49), PDF p. 8 |
| `H=(|1><2|+|2><1|)/2`, `rho(0)=|1><1|` | exponentiate defining `U(t)=exp(-itH)`, not inconsistent expanded Eq. (58), then evaluate both bridges | no dissipator | qutrit `L1=sin^2(t/2)/2`, `L2=sin^2(t/2)`, `C_L=abs(sin t)` | Sec. VI.B, Eqs. (57), (59)--(61), PDF p. 9 |
| same pure unitary with coefficient `theta` and unit duration | identify `t=2 theta` | Hamiltonian normalizations compared explicitly | `L1=sin^2(theta)/2`, `L2=sin^2(theta)`, state `C_L=abs(sin(2 theta))` | Eqs. (57), (59)--(61), PDF p. 9 |
| `A21`, `A12`, rates `gamma1`, `gamma2` | exponentiate `gamma1 D[A21] + gamma2 D[A12]` using the explicit `D[A]` convention from Eqs. (26)--(27) | no Hamiltonian; do not read conflicted Eq. (70) literally | Eqs. (73)--(74) rates | Sec. IV, Eqs. (26)--(27), PDF p. 4; Sec. VI.C.1, Eqs. (72)--(74), PDF p. 11 |
| simultaneous exchange and both ladder jumps | compare exact `exp[dt(mathcal H+mathcal D)]` rates with sum of separately exponentiated rates | jump-operator hypothesis of Lemma 2 | difference scales as third order at short time and is nonzero at finite time | Sec. VI.C, Lemma 2 and Eq. (71), PDFs pp. 10--11; Appendix E, PDF p. 16 |

Numerical replay pins:

- for `t = 0.1, 0.7, 1.4`, the largest absolute error across VOR Eqs. (59)--(61) and
  `2 L1 = L2` was at most `2.22e-16`; this follows the defining exponential and exposes, rather
  than repairs in the source record, the missing `-i` in expanded Eq. (58);
- for `gamma1=0.07`, `gamma2=0.11`, and `t=0.8`, the hand-typed channel gave
  `L1=0.026077382321821253` and `L2=0.08195748729715248`, agreeing with VOR
  Eqs. (73)--(74) within `4.17e-17`;
- for simultaneous `H=0.37(|1><2|+|2><1|)`, `gamma1=0.07`, and `gamma2=0.11`, the
  maximum difference between exact combined rates and the sum of component rates was
  `2.24e-11`, `2.23e-8`, `2.22e-5`, and `1.98e-2` at `dt=1e-3`, `1e-2`, `1e-1`, and `1`,
  respectively. This is consistent with the second-order statement and falsifies exact finite-time
  additivity.

## Coverage ledger

| assigned row | VOR says | VOR does not say | status |
|---|---|---|---|
| arbitrary-channel `L1/L2` bridge | Eq. (2) defines two projector-average rates | neither rate is a device-independent parameter | closed |
| state coherence bridge | Eqs. (33)--(34) define `C_L(rho)` for one state | one fixed input is not a channel average | closed |
| channel coherent rates | Eqs. (42)--(43) define Haar averages over diagonal pure-state inputs | current fixed-input code is not either average | closed definition; implementation mismatch |
| Proposition 2 bound | main text states the upper bound | Appendix C has projector, equality, and unstated operator-basis-condition conflicts | closed as stated proposition; proof chain internally incomplete |
| DLM twirl | Eqs. (48), (53)--(55) define the target model and state preserved diagnostics | Eq. (49) does not uniquely normalize independent `U_2,V_2` | contradicted internally as an executable twirl |
| pure exchange model | Eqs. (57), (59)--(61) state generator, rates, and fixed-state coherence | expanded Eq. (58) omits `-i`; closed forms contain no dissipator | closed after explicit exponential replay; printed propagator contradicted internally |
| simple dissipative model | Eqs. (72)--(75) give two jumps and exact rates | it is separate from the exchange example | closed |
| simultaneous unitary plus dissipation | Eq. (69) provides the unitary generator and the source intends a Lindblad envelope; Lemma 2 states second-order rate additivity | Eq. (70) is not a closed trace-preserving expression when read literally; Appendix E collapses a general ladder sum to one term; no unique named three-parameter channel or exact finite-time additive formula | stated envelope/additivity only with both proof-conflict warnings; missing canonical naming |
| numerical scale | Sec. IV reports a pulse- and transmon-specific simulation | no universal `theta`, jump-rate, or `L1/L2` intervals | missing; later scale sources remain open |
| coherence inference from population rates | Introduction calls `L1+L2` a misnomer for coherence; DLM retains rates while removing coherence | population rates alone do not identify coherent leakage | contradicted if asserted |
| simple LRB decay | leakage-subspace depolarization is a key assumption | insufficient twirling can leave oscillations and overestimate rates | closed limitation |

## Current implementation classification

### Paper-defined mathematics retainable under neutral names

- direct-sum projector definitions of `L1` and `L2` currently exposed through `wg_rates`;
- off-block trace norm inside `coherence_of_leakage`, only when its input state is explicit;
- pure exchange mapping `t=2 theta`, based on the defining exponential and VOR
  Eqs. (59)--(61), with the Eq. (58) print conflict retained;
- two ladder-jump directions;
- general exact GKSL construction as a specialization of distinct generators in
  Eqs. (69)--(70).

### Current-simulator design, not a paper-defined named channel

- choosing `theta`, `g_seep`, and `g_heat` simultaneously and evolving for unit duration;
- treating those values as one public channel family and attaching author initials to APIs,
  schemas, manifests, tests, source-coupling fields, services, and presets;
- target sweeps, defaults, bisection coordinate, and leaked-readout POVM;
- treating fixed-input `C_L(E(|1><1|))` as a generic channel coherence indicator.

## P0 findings before any source edit

1. **Twelve load-bearing VOR source conflicts remain.** Appendix C Eq. (C5) conflicts with Eq. (C6), Eq. (C11)
   changes an established upper bound to equality, Eq. (49) has an unresolved double-index
   normalization, expanded Eq. (58) omits the `-i` required by `exp(-itH)`, Appendix A Eq. (A16)
   duplicates one cross term, Eq. (70) leaves its anticommutator outside the explicit
   `sum_k gamma_k` scope, Eq. (D2) omits adjoint dimension factors, the following Appendix D action
   conflicts with Eq. (D3), Appendix C omits a required operator-basis condition, Appendix A/C use
   an impossible `d1-1` operator-basis upper limit, Eq. (D1) names undefined `E_m` adjoint, and
   Appendix E collapses a general ladder sum to one term. No implementation may cite a silently
   repaired chain as an exact paper oracle.
2. **Over-attributed product name.** The paper supplies definitions, examples, and a general
   Lindblad envelope, but never names the current exact three-parameter specialization a
   "Wood--Gambetta channel". Author-specific public vocabulary must be hard-cut to physical,
   neutral names while exact citations remain attached to formulas.
3. **False global biconditional.** The current docstring says `theta>0` implies `C_L>0`. VOR
   Eq. (61), under `t=2 theta`, gives `C_L=abs(sin(2 theta))`; at `theta=pi/2` it is zero although
   `theta>0`. Current code returns `3.3306690738754696e-16` at that point. The statement is true
   only inside a declared small-angle interval excluding zero.
4. **Fixed-state/channel mismatch.** VOR Eqs. (42)--(43) consistently define channel coherent
   rates as Haar averages. `coherence_of_leakage` instead computes VOR Eq. (34) for fixed input
   `|1><1|`. At `theta=pi/2`, that input ends wholly in `|2>` and gives zero cross-block
   coherence, while `(|0>+|1>)/sqrt(2)` evolves to an equal `|0>`/`|2>` superposition with state
   `C_L=1`. The API/artifact field must identify its state and input or implement the actual
   channel average.
5. **Incorrect scope of the pure-exchange rate.** `L1=sin^2(theta)/2` is exact for the pure
   unitary after `t=2 theta`; it is not exact for the simultaneous dissipative channel. Solver
   prose currently blurs the regimes.
6. **Unproved bisection contract.** The combined-channel solver assumes monotonicity on
   `[0, pi/2]` and checks only its upper endpoint. With heating, the lower endpoint can already
   have positive `L1`; a target below that baseline is not rejected. For
   `target=0`, `g_seep=0`, `g_heat=0.1`, it returns `theta=0`, but reevaluation gives
   `L1=0.04758129098202021`.

No `src/**` file is changed in this literature subphase. A later explicitly confirmed source-edit
phase should neutralize author-based vocabulary, make the fixed-state observable explicit, remove
the false biconditional, repair the solver contract, and add counterexamples at `theta=pi/2` and
below a nonzero-heating baseline. Existing implementation-consistency tests remain useful after
neutral renaming, but they are not independent literature oracles.

## Review and admission

- superseded v1 draft: two source-only review rounds failed; it was never placed in the corpus;
- reason for supersession: the VOR fixes the v1 main-text coherent-rate inputs and substantially
  renumbers sections, equations, pages, and assumptions;
- VOR source-only note:
  `docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md`;
- first VOR reviewer: `wood_source_review`, FAIL on candidate
  `8aad0354132cfe47931639f21caf5489253f8de3db8e29f4d629bb2222b6083f` because Eq. (70) and the
  Appendix D adjoint-action conflict were missing;
- second VOR reviewer: PASS on revision
  `cb4accbab66649de325d1cda29fcc32e2891b25bf606d943504b0e7c60083557`, superseded before
  admission when the independent adversarial scan found the Appendix C/D/E gaps;
- third VOR reviews: FAIL on revision
  `3fbe5c35032f533bc6f481b9512dc9461a6f25792f81d93302ba76050e2f57b2` because
  rank-one Haar projectors were mislabeled "diagonal", the operator-basis cardinality conflict was
  missing, and Eq. (D1)'s undefined iteration symbol remained unisolated;
- revised VOR note shape: 38 one-record `paper_fact` sections, two `literature_gap` sections, and 13
  relations;
- fourth VOR source-only reviews: PASS by `wood_source_review` and `wood_local_inventory` on
  candidate `aa6503d7f17d17e84154354b59f00d40569533e7482a51105fd31d9809e08141`;
- reviewed shape: 38 `paper_fact`, two `literature_gap`, 13 relations; no dangling relation and no
  source-only purity violation;
- source-only admission decision: PASS. The closed packet hash is bound in the note metadata;
  manifest publication remains conditional on the subsequent artifact-verified schema gate.

## Closure status

`closed_for_wood_source_attribution`. The bounded attribution audit separates Eq. (2), Eq. (34),
Eqs. (42)--(43), the replayed pure-exchange
rates, the simple dissipative rates, and the general Lindblad envelope by evidentiary scope; it also
preserves all twelve load-bearing VOR source conflicts. The broader qutrit parameter-scale closure remains open
until separately assigned sources are read. No device-calibrated scale claim is authorized.
