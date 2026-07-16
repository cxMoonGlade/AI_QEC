+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.1103/PhysRevA.97.032306"
source_version = "version-of-record"
source_uri = "https://doi.org/10.1103/PhysRevA.97.032306"
source_artifact = "docs/papers/wood_gambetta_leakage_characterization_pra_97_032306.pdf"
source_sha256 = "66a9d749cdb5841b3cc565debc33bd17fcb46946c13d374ccd274fc87234169b"
title = "Quantification and Characterization of Leakage Errors"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/WOOD_GAMBETTA_1704_03081_CLAIM_AUDIT_2026-07-15.md"
audit_packet_sha256 = "7c0f07ab2270619e580b927187a34d68f7bd95a122a9ac7e477a655b0c9808bb"
admission_status = "source_only_reviewed"
admission_reviewer = "wood_vor_round4_dual_review"
admission_date = "2026-07-15"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

[[relations]]
predicate = "defines"
object_id = "state-leakage"
object_type = "observable"
object_label = "state leakage"
fact_id = "fact.state-leakage"

[[relations]]
predicate = "defines"
object_id = "leakage-rate"
object_type = "observable"
object_label = "leakage rate"
fact_id = "fact.channel-transfer-rates"

[[relations]]
predicate = "defines"
object_id = "seepage-rate"
object_type = "observable"
object_label = "seepage rate"
fact_id = "fact.channel-transfer-rates"

[[relations]]
predicate = "defines"
object_id = "coherence-of-leakage"
object_type = "observable"
object_label = "coherence of leakage"
fact_id = "fact.state-coherence"

[[relations]]
predicate = "defines"
object_id = "channel-coherent-rates"
object_type = "observable"
object_label = "channel coherent leakage and seepage rates"
fact_id = "fact.channel-coherent-rate-definitions"

[[relations]]
predicate = "supports"
object_id = "proposition-2-bound"
object_type = "theorem"
object_label = "Proposition 2 bound"
fact_id = "fact.channel-rate-bound-statement"

[[relations]]
predicate = "defines"
object_id = "depolarizing-leakage-extension"
object_type = "model"
object_label = "depolarizing leakage extension"
fact_id = "fact.dle-definition"

[[relations]]
predicate = "defines"
object_id = "depolarizing-leakage-model"
object_type = "model"
object_label = "depolarizing leakage model"
fact_id = "fact.dlm-definition"

[[relations]]
predicate = "limits"
object_id = "dlm-twirl"
object_type = "limitation"
object_label = "DLM twirl"
fact_id = "fact.dlm-twirl-conflict"

[[relations]]
predicate = "defines"
object_id = "unitary-leakage-model"
object_type = "model"
object_label = "unitary leakage model"
fact_id = "fact.exchange-generator"

[[relations]]
predicate = "uses"
object_id = "lindblad-leakage-model"
object_type = "model"
object_label = "Lindblad leakage model"
fact_id = "fact.lindblad-envelope"

[[relations]]
predicate = "defines"
object_id = "simple-dissipative-leakage"
object_type = "model"
object_label = "simple dissipative leakage model"
fact_id = "fact.simple-dissipator-jumps"

[[relations]]
predicate = "limits"
object_id = "lrb-depolarization-assumption"
object_type = "limitation"
object_label = "leakage randomized benchmarking decay model"
fact_id = "fact.lrb-depolarization-assumption"
+++
# Full-text review -- Wood and Gambetta, "Quantification and Characterization of Leakage Errors"

## Source identity [paper_fact]

Fact ID: fact.source-identity
Source locator: PDF p. 1, title, author, publication, and DOI block
PDF page: 1
Claim: Christopher J. Wood and Jay M. Gambetta authored "Quantification and Characterization of Leakage Errors," published in Physical Review A 97, 032306 on March 8, 2018 with DOI 10.1103/PhysRevA.97.032306.

The version of record contains seventeen pages and Appendices A through E.

## Scientific scope [paper_fact]

Fact ID: fact.scientific-scope
Source locator: Abstract and Sec. I, PDF p. 1
PDF page: 1
Claim: The article develops leakage and seepage metrics, coherent-leakage quantities, a leakage randomized benchmarking protocol, and example leakage models for systems encoded in a subspace of a larger state space.

The examples include superconducting-qubit control and thermal relaxation.

## State leakage [paper_fact]

Fact ID: fact.state-leakage
Source locator: Sec. II, Eq. (1)
PDF page: 2
Claim: State leakage is the population outside computational subspace `X_1`, defined by `L(rho) = Tr[1_2 rho] = 1 - Tr[1_1 rho]` on the direct sum `X = X_1 direct-sum X_2`.

The projectors `1_1` and `1_2` act on subspaces of dimensions `d_1` and `d_2`, respectively.

## Channel transfer rates [paper_fact]

Fact ID: fact.channel-transfer-rates
Source locator: Sec. II, Eq. (2)
PDF page: 2
Claim: For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces.

The two quantities distinguish average population transfer out of and back into the computational
subspace.

## Combined-rate insufficiency [paper_fact]

Fact ID: fact.combined-rate-insufficiency
Source locator: Sec. II, paragraph following Eqs. (5)--(8)
PDF page: 2
Claim: The source states that knowing only the combined rate `L_1 + L_2` is insufficient to quantify gate error accurately.

It therefore proposes retaining `L_1`, `L_2`, and average gate error as distinct characterization
parameters.

## Unital transfer invariant [paper_fact]

Fact ID: fact.unital-invariant
Source locator: Sec. II, footnote 1
PDF page: 3
Claim: A unital leakage map satisfies the transfer invariant `d_1 L_1(E) = d_2 L_2(E)`.

Footnote 1 derives the identity directly from Eq. (2) and unitality of `E`.

## Population rates are not coherence [paper_fact]

Fact ID: fact.rates-not-coherence
Source locator: Sec. I, final overview paragraph
PDF page: 1
Claim: The article calls the use of `L_1 + L_2` as a coherence measure a misnomer because leakage and seepage can arise from purely incoherent thermal relaxation.

Section V introduces distinct quantities for cross-subspace coherence.

## State coherence of leakage [paper_fact]

Fact ID: fact.state-coherence
Source locator: Sec. V.A, Eqs. (30)--(34)
PDF page: 6
Claim: The coherence of leakage of a state is `C_L(rho) = ||P_C(rho)||_1`, where `P_C(rho) = 1_1 rho 1_2 + 1_2 rho 1_1` is the cross-subspace block.

The trace norm compares the state with its incoherent block projection.

## State-coherence bound [paper_fact]

Fact ID: fact.state-coherence-bound
Source locator: Sec. V.A, Proposition 1 and Eqs. (35)--(37)
PDF page: 7
Claim: Proposition 1 states `C_L(rho) <= 2 sqrt(p_l(1-p_l))`, with equality for the pure-state construction in Eqs. (35)--(37).

Here `p_l = L(rho)` is the state's leaked population.

## Channel coherent-rate definitions [paper_fact]

Fact ID: fact.channel-coherent-rate-definitions
Source locator: Sec. V.B, Eqs. (42)--(43)
PDF page: 7
Claim: The channel coherent leakage and seepage rates are Haar averages of `C_L(E(|psi_j><psi_j|))` over rank-one projectors formed from all Haar-distributed pure states in subspaces `X_j`, for `j=1,2`.

These are channel averages and are distinct from evaluating state coherence for one fixed input.

## Appendix-C projector conflict [paper_fact]

Fact ID: fact.appendix-c-projector-conflict
Source locator: Appendix C, Eqs. (C5)--(C6)
PDF page: 15
Claim: Eq. (C5) writes the squared leaked-population term with projector `1_1`, while the immediately following Eq. (C6) uses `1_2 tensor 1_2` for the same term.

This is a source-internal symbol conflict on the proof page.

## Appendix-C equality conflict [paper_fact]

Fact ID: fact.appendix-c-equality-conflict
Source locator: Appendix C, Eqs. (C2)--(C4) and (C11)
PDF page: 16
Claim: Eq. (C11) prints an equality for `C_L1` after Eqs. (C2)--(C4) established only an upper-bound chain.

The final inequality in Eq. (C12) is printed as the bound stated in Proposition 2.

## Appendix-C operator-basis condition [paper_fact]

Fact ID: fact.appendix-c-operator-basis-condition
Source locator: Appendix C, Eqs. (C9)--(C10)
PDF page: 15
Claim: Eqs. (C9)--(C10) expand the SWAP operator with `A_j tensor A_j` after specifying only an orthonormal operator basis, without stating the Hermitian or self-dual basis condition needed to omit conjugation or an adjoint.

A Hermitian orthonormal basis can supply the displayed identity, but that additional basis choice is
not stated in the proof.

## Operator-basis cardinality conflict [paper_fact]

Fact ID: fact.operator-basis-cardinality-conflict
Source locator: Appendix A, paragraph following Eq. (A18); Appendix C, Eqs. (C9)--(C10)
PDF page: 14
Claim: Appendix A indexes an operator basis for `L(X_1)` only from `j=0` through `d_1-1`, and Appendix C likewise sums its nonidentity elements only through `d_1-1`, although that operator space has dimension `d_1^2`.

The qubit example on PDF p. 14 lists the four-element basis `{1_1,X,Y,Z}/sqrt(2)` for `d_1=2`,
directly contradicting the printed two-element index range. The same cardinality error propagates
into the displayed identity-superoperator and SWAP sums.

## Channel-rate bound statement [paper_fact]

Fact ID: fact.channel-rate-bound-statement
Source locator: Sec. V.B, Proposition 2
PDF page: 7
Claim: The Proposition 2 bound states `C_Lj(E) <= 2 sqrt(L_j(E)(1-L_j(E)))` for the channel coherent leakage and seepage quantities.

This record preserves the proposition's stated inequality; the separate Appendix-C records preserve
the printed proof inconsistencies.

## Depolarizing extension definition [paper_fact]

Fact ID: fact.dle-definition
Source locator: Sec. VI.A.2, Eqs. (46)--(47)
PDF page: 8
Claim: The depolarizing leakage extension of a computational-subspace channel is the model in Eq. (46), parameterized by leakage and seepage rates and completely depolarizing maps between the two subspaces.

The source abbreviates this construction as DLE.

## Depolarizing extension coherence removal [paper_fact]

Fact ID: fact.dle-coherence-removal
Source locator: Sec. VI.A.2, paragraphs following Eq. (47) and Lemma 1
PDF page: 8
Claim: The source states that the DLE removes cross-subspace coherence and leakage-subspace memory, so its output has zero coherence of leakage.

Lemma 1 states the resulting exponential population-accumulation model. The next three records
preserve conflicts in its Appendix D derivation.

## Appendix-D iteration-symbol conflict [paper_fact]

Fact ID: fact.appendix-d-iteration-symbol-conflict
Source locator: Appendix D, Eq. (D1), compared with Eq. (D2)
PDF page: 16
Claim: Eq. (D1) writes the iterated adjoint as `(E_m adjoint)^m`, but `E_m` is not defined there and the immediately following Eq. (D2) instead defines `E_L` adjoint for the DLE used throughout the proof.

The surrounding equalities require `(E_L adjoint)^m`; this record preserves the printed subscript
rather than silently changing it.

## Appendix-D adjoint-normalization conflict [paper_fact]

Fact ID: fact.appendix-d-adjoint-normalization-conflict
Source locator: Appendix D, Eq. (D2), compared with Sec. VI.A.2 Eq. (47) and Appendix A Eq. (A18)
PDF page: 16
Claim: Eq. (D2) replaces each normalized depolarizing map `D_ij` by `D_ji` under the adjoint without the dimension factor required by the source's own definition, namely `D_ij` adjoint `= (d_j/d_i) D_ji`.

The omission vanishes only when `d_1=d_2`; the qutrit split discussed by the source has
`d_1=2,d_2=1`. The following matrix Eq. (D3) instead matches the correctly normalized action on
subspace projectors.

## Appendix-D adjoint-action conflict [paper_fact]

Fact ID: fact.appendix-d-adjoint-action-conflict
Source locator: Appendix D, displayed line following Eq. (D2), compared with Eq. (D3)
PDF page: 16
Claim: The displayed action of `E_L` adjoint prints the leakage-subspace coefficient as `L_1 beta + (1-L_2) beta`, whereas the immediately following matrix in Eq. (D3) requires `L_2 alpha + (1-L_2) beta`.

The printed action and matrix are internally inconsistent; the later Lemma 1 derivation follows the
matrix rather than the displayed coefficient.

## Depolarizing-model definition [paper_fact]

Fact ID: fact.dlm-definition
Source locator: Sec. VI.A.3, Eq. (48)
PDF page: 8
Claim: The depolarizing leakage model is the DLE special case in Eq. (48) whose computational-subspace component is depolarizing.

The source abbreviates this model as DLM.

## Printed DLM-twirl conflict [paper_fact]

Fact ID: fact.dlm-twirl-conflict
Source locator: Sec. VI.A.3, Eq. (49) and its preceding paragraph
PDF page: 8
Claim: The printed DLM twirl introduces independent leakage-subspace unitaries `U_2,V_2` and sums over both, while Eq. (49) divides by only one factor of `|P_2|`.

The same paragraph calls the result a DLE projection even though the surrounding subsection and
resulting channel identify a DLM. The operation is recorded as internally ambiguous rather than
silently normalized.

## Depolarizing-model diagnostic preservation [paper_fact]

Fact ID: fact.dlm-diagnostic-preservation
Source locator: Sec. VI.A.3, Eqs. (53)--(55)
PDF page: 9
Claim: The source states that the resulting depolarizing leakage model preserves the original channel's average gate fidelity, leakage rate, and seepage rate.

This stated preservation result is recorded separately from the ambiguous twirl printed in Eq. (49).

## Exchange generator [paper_fact]

Fact ID: fact.exchange-generator
Source locator: Sec. VI.B, Eqs. (57)--(58), first equality
PDF page: 9
Claim: The unitary leakage model starts from `H = (|1><2| + |2><1|)/2` and defines its propagator by `U(t) = exp(-i t H)`.

The Hamiltonian exchanges one computational state and one leakage state.

## Printed exchange-propagator conflict [paper_fact]

Fact ID: fact.exchange-propagator-conflict
Source locator: Sec. VI.B, Eq. (58), expanded expression
PDF page: 9
Claim: The expanded expression printed in Eq. (58) omits the factor `-i` from its sine cross term and therefore does not equal the preceding `exp(-i t H)` expression.

The defining exponential and the expanded expression are kept distinct.

## Exchange transfer rates [paper_fact]

Fact ID: fact.exchange-rates
Source locator: Sec. VI.B, Eqs. (59)--(60)
PDF page: 9
Claim: For the exchange evolution, the source states `L_j(U(t)) = sin^2(t/2)/d_j` and `L(rho_1(t)) = sin^2(t/2)<1|rho_1|1>`.

For a qutrit split with `d_1=2` and `d_2=1`, the stated channel rates satisfy the unital invariant.

## Exchange state coherence [paper_fact]

Fact ID: fact.exchange-state-coherence
Source locator: Sec. VI.B, Eq. (61)
PDF page: 9
Claim: For the initial state `rho_1(0)=|1><1|`, the source states that the exchange evolution gives `C_L(rho_1(t)) = |sin(t)|`.

This is a state quantity for one declared input, not a channel-level average.

## General weak unitary leakage [paper_fact]

Fact ID: fact.weak-unitary
Source locator: Sec. VI.B.2, Eqs. (66)--(68)
PDF page: 10
Claim: For a time-dependent Hamiltonian, the leading leakage and seepage contribution is second order in time and is determined by the cross-subspace block of the first-order average Hamiltonian.

The result is a short-time Dyson approximation, unlike the exact exchange-rate statement.

## Lindblad envelope [paper_fact]

Fact ID: fact.lindblad-envelope
Source locator: Sec. VI.C, Eqs. (69)--(70)
PDF page: 10
Claim: A Lindblad leakage model is written as `E = exp[t(mathcal H + mathcal D)]`, where superoperator `mathcal H` acts as `mathcal H(rho) = -i[H,rho]` for Hamiltonian `H` and `mathcal D` is presented as the dissipative generator.

The source distinguishes the Hamiltonian operator from the two generators and says physical leakage
can combine unitary and dissipative contributions. The next record preserves the printed ambiguity
inside `mathcal D` rather than silently replacing it with the standard expression.

## Printed Lindblad-dissipator conflict [paper_fact]

Fact ID: fact.lindblad-dissipator-print-conflict
Source locator: Sec. VI.C, Eq. (70), compared with Sec. IV Eqs. (26)--(27) and Appendix E
PDF page: 10
Claim: In Eq. (70), the printed sum over `k` and rate `gamma_k` apply explicitly only to the recycling term, while the anticommutator term retains an unbound `k` and no `gamma_k`.

This conflicts with the source's earlier `gamma D[A]` convention in Eqs. (26)--(27) and its use of
per-jump `D[A_k]` in Appendix E. The standard trace-preserving form can be inferred from those
locations but is not silently substituted into Eq. (70).

## Second-order component additivity [paper_fact]

Fact ID: fact.second-order-additivity
Source locator: Sec. VI.C, Lemma 2 and Eq. (71); Appendix E
PDF page: 10
Claim: When every Lindblad jump operator `A_k` has the stated fixed-shift ladder form, the `L_1` and `L_2` rates of `exp[Delta t(mathcal H+mathcal D)]` are additive between the unitary and dissipative components to second order in `Delta t`.

Appendix E on PDF p. 16 presents a cancellation argument for the mixed second-order terms; the
lemma does not state exact finite-time additivity. The next record preserves a scope error inside
that printed argument.

## Appendix-E ladder-sum conflict [paper_fact]

Fact ID: fact.appendix-e-ladder-sum-conflict
Source locator: Appendix E, Eqs. (E2)--(E4)
PDF page: 16
Claim: Although Eq. (E2) permits a fixed-shift jump operator with multiple nonzero coefficients `alpha_s`, Eq. (E3) replaces the projected product by one term `|alpha_s|^2 |s><s|` "for some s" rather than the allowed diagonal sum.

The real-trace conclusion can be recovered term by term, but the single-term equality printed in
Eq. (E3) does not cover the full operator class stated in Lemma 2.

## Simple dissipative jump model [paper_fact]

Fact ID: fact.simple-dissipator-jumps
Source locator: Sec. VI.C.1, Eq. (72)
PDF page: 11
Claim: The simple dissipative leakage model uses jump `A_21 = |2><1|` with rate `gamma_1` for leakage and jump `A_12 = |1><2|` with rate `gamma_2` for seepage.

This subsection contains no simultaneous exchange Hamiltonian.

## Simple dissipative rates [paper_fact]

Fact ID: fact.simple-dissipator-rates
Source locator: Sec. VI.C.1, Eqs. (73)--(74)
PDF page: 11
Claim: The simple two-jump dissipative channel has `L_1 = gamma_1[1-exp(-t(gamma_1+gamma_2))]/[d_1(gamma_1+gamma_2)]` and the analogous `L_2` expression with `gamma_2/d_2`.

These are exact finite-time expressions for the purely dissipative example.

## LRB depolarization assumption [paper_fact]

Fact ID: fact.lrb-depolarization-assumption
Source locator: Sec. III, assumptions (i)--(ii)
PDF page: 3
Claim: The leakage randomized benchmarking decay model requires computational-subspace twirling to average cross-subspace coherence and the leakage-subspace population to be depolarized.

The source says violations can produce coherence buildup and leakage-subspace memory effects.

## LRB derivation assumptions [paper_fact]

Fact ID: fact.lrb-derivation-assumptions
Source locator: Appendix A, Assumptions 1--3
PDF page: 13
Claim: Appendix A derives the decay model under gate-independent noise, averaging away cross-subspace coherence, and depolarization of the leakage subspace.

Assumptions 2 and 3 appear on PDF p. 14; the source notes where these conditions may hold or fail.

## Printed LRB cross-term conflict [paper_fact]

Fact ID: fact.lrb-cross-term-conflict
Source locator: Appendix A, Eq. (A16), compared with Eq. (A17) and Sec. VI.A.3 Eq. (50)
PDF page: 14
Claim: Eq. (A16) repeats the cross term `D_1 E D_2` twice and omits `D_2 E D_1`, although Eq. (A17) immediately contains both directional transfer maps and Eq. (50) prints both cross terms.

This source-internal duplication is retained as printed and is not used as an independent derivation
of the DLM channel.

## LRB failure consequence [paper_fact]

Fact ID: fact.lrb-failure-consequence
Source locator: Sec. VII, third paragraph
PDF page: 12
Claim: If leakage-subspace depolarization fails in the presence of coherent leakage, the source says oscillations can appear around the exponential decay model and can overestimate leakage and seepage rates.

This limitation is stated for the characterization protocol, not as a property of every leakage
channel.

## No canonical combined parameterization [literature_gap]

Fact ID: gap.canonical-combined-parameterization
Source locator: Sec. VI.B--C, Eqs. (57)--(74)
PDF page: 11
Claim: The source does not define a uniquely named exact channel with one exchange coefficient, two simultaneous jump rates, unit evolution time, and a canonical calibration of those three parameters.

Gap scope: source_local

It provides a general Lindblad envelope and separate unitary and dissipative examples, with a
second-order statement about their rate contributions.

## No universal numerical regime [literature_gap]

Fact ID: gap.universal-numerical-regime
Source locator: Sec. IV, Eqs. (19)--(29) and Figs. 1--3
PDF page: 4
Claim: The source does not report device-independent numerical intervals for an exchange angle, two jump rates, or leakage and seepage rates.

Gap scope: source_local

Its numerical results on PDF pp. 4--7 use a specified simulated transmon, pulse family, pulse
length, relaxation parameters, and randomized-benchmarking setup.
