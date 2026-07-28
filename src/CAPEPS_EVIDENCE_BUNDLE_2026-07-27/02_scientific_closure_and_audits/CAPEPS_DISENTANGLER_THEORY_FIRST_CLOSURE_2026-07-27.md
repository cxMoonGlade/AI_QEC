# CAPEPS disentangler theory-first closure packet

Date: 2026-07-27
Status: `OPEN`
Design maturity: `EXACT_SMALL_QUBIT_DESIGN_FROZEN`
closure_status: `open`
theory-first decision: `CODE_BLOCKED`
Scope: all-qubit CAPEPS two-site Clifford refactor search; separate prime-qutrit/SDIM theory lane

This packet records the theory-first result obtained before adding an optimizer. External academic batch retrieval through AnySearch was explicitly authorized by the user on 2026-07-27. Search results were used only to locate sources; the claims below were checked against primary papers, supplements, and pinned source code.

The mathematical design and its negative boundaries are closed far enough to
freeze an exact-small experiment. Its minimal qubit source set is now
current-schema admitted and artifact-verified. That is still not a
repository-level `theory-first` pass: the proposed Rényi-2 score has no current
owner plus independent value test in `docs/METRICS.md`, while qutrit and generic
scalable-PEPS evidence lanes remain open. Consequently this packet grants no
new `src/**` work.

## 1. Frozen question charter

Primary question:

> Can a two-site Clifford search reduce the residual complexity of
> \(|\Psi\rangle=C|\phi\rangle_{\rm PEPS}\) without changing the represented physical state, and can the search be reduced to a complete finite catalogue?

Secondary question:

> What can SDIM support for a later prime-qutrit implementation, without conflating it with the current qubit PEPS residual?

Out of scope: a field-wide novelty claim, a generic scalable PEPS error certificate, composite local dimension, qutrit leakage, logical-error-rate or threshold claims.

Decision and consequence:

- If the analytic falsifier, all-720 differential, 20-key orbit audit, and paired-ray invariant all pass after the source and metric gates close, a later reviewed phase may consider only the exact-small catalogue implementation. Otherwise the quotient, score, or refactor claim is rejected; no optimizer result may be reported.

Importance × attackability:

- High × high. A quotient-side or phase error changes candidate completeness or the physical state, while the complete two-qubit group has only 720 phase-free elements and admits exhaustive independent dense disconfirmation.

Reusable object and test:

- The reusable objects are the frozen post-local canonical key, the independent all-720 differential, the paired physical-ray invariant, and the F0 CNOT/input-local counterexample.

Alternative formulations retained:

- exhaustive all-720 search as the primary baseline;
- no-optimizer identity behavior as a negative baseline;
- the full double quotient as a rejected fixed-input formulation;
- exact finite-network fidelity separated from any approximate-environment diagnostic.

Kill conditions:

- Any open load-bearing source admission or metric owner/value test keeps code blocked. Any failure of orbit size, score completeness, tableau round-trip, phase lift, or paired-ray invariance kills the exact-small claim. Absence of an independently certified scalable PEPS contraction bound kills every scalable-correctness extrapolation.

## 2. Top-down formula spine

### L0 — hybrid state

The represented state is

\[
|\Psi\rangle=C|\phi\rangle .
\tag{1}
\]

GCAMPS gives this structure for an MPS residual (Harper et al., arXiv:2511.06672v2, Sec. 3 and Fig. 3, PDF p. 5). Replacing MPS by PEPS is a project proposal, not a result established by that paper.

### L1 — operation fork

For a physical Clifford \(G\),

\[
G|\Psi\rangle=(GC)|\phi\rangle .
\tag{2}
\]

For a small-support non-Clifford

\[
U=\sum_j\alpha_jP_j,
\qquad
\widetilde P_j=C^\dagger P_jC,
\]

one has

\[
UC|\phi\rangle
=C\left(\sum_j\alpha_j\widetilde P_j\right)|\phi\rangle .
\tag{3}
\]

The complex amplitudes and Pauli phases are retained. Replacing them by probabilities would be a Pauli twirl and a different channel.

### L2 — exact paired refactor

For any unitary Clifford \(Q\),

\[
(C,|\phi\rangle)
\longmapsto
(CQ^\dagger,Q|\phi\rangle),
\qquad
(CQ^\dagger)Q|\phi\rangle=C|\phi\rangle .
\tag{4}
\]

This is the main correctness separation: a bad optimizer can fail to improve efficiency, but cannot change the physical state if both updates are exact and atomic. Approximation enters only through residual operator construction, contraction, or compression.

### L3 — the quotient must be output-local and one-sided

Let \(G_q\) be the phase-free two-qudit Clifford group and
\(H_q=G_q^{(1)}\otimes G_q^{(1)}\) its local subgroup. For a fixed input and any score depending only on a registered bipartite Schmidt spectrum,

\[
J(LQ|\phi\rangle)=J(Q|\phi\rangle),
\qquad L=L_A\otimes L_B\in H_q .
\tag{5}
\]

Therefore candidates are post-action local cosets. In a standard column-vector convention this is the left quotient \(H_q\backslash G_q\). A row-action tableau convention may reverse the matrix-side label, so the implementation term must be `PostLocalCosetRepresentative`, not merely “left class.”

Input-side local multiplication cannot generally be removed:

\[
J(QL|\phi\rangle)\ne J(Q|\phi\rangle).
\tag{6}
\]

Counterexample:

\[
Q=\operatorname{CNOT},\quad
Q^{\prime}=\operatorname{CNOT}(H\otimes I),\quad
|\phi\rangle=|00\rangle .
\]

Then \(Q|00\rangle=|00\rangle\), while
\(Q^{\prime}|00\rangle=(|00\rangle+|11\rangle)/\sqrt2\). Thus the double-sided relation written in Masot-Llima et al., arXiv:2602.15942v2, Sec. II.B, PDF p. 3, cannot justify 20 candidates for a generic fixed-input objective. The actual two-qubit local double quotient has four classes, as catalogued by Córcoles et al., arXiv:1210.7011v2, Supplement.

### L4 — why the counts are 20 and 90

For qubits, after quotienting Pauli phases,

\[
|\operatorname{Sp}(4,\mathbb F_2)|=720,
\qquad
|\operatorname{Sp}(2,\mathbb F_2)|^2=6^2,
\]

so

\[
|H_2\backslash G_2|=720/6^2=20.
\tag{7}
\]

Equivalently, using projective Clifford orders,
\(11520/24^2=20\).

For qutrits,

\[
|\operatorname{Sp}(2n,\mathbb F_q)|
=q^{n^2}\prod_{k=1}^{n}(q^{2k}-1),
\tag{8}
\]

hence

\[
|\operatorname{Sp}(4,\mathbb F_3)|=51840,
\quad
|\operatorname{Sp}(2,\mathbb F_3)|^2=24^2=576,
\quad
|H_3\backslash G_3|=90.
\tag{9}
\]

Kim, Oh, and Kim, arXiv:2607.03939v1, Supplement S1 Eqs. (S6)–(S7), explicitly call these left cosets. Supplement Table S2 groups the 90 gates into ten AKLT response types, but those ten types are not a generic ten-gate catalogue. Its majorization lemma and optimality theorem apply to the stated AKLT tensor family and parameter interval, not generic MPS or PEPS.

### L5 — executable qubit catalogue and independent reconstruction

Chang et al., arXiv:2606.12056v1, Eq. (10), Appendix Algorithms 1–2, and Theorem 1 Eqs. (A14)–(A30), provide an iff class criterion. With

\[
S=\begin{bmatrix}A&B\\C&D\end{bmatrix},
\qquad
Q_0=\bigoplus_i\begin{bmatrix}0&1\\1&0\end{bmatrix},
\]

the hash packs

\[
T_1=AQ_0A^T,
\qquad
T_2=AQ_0C^T,
\qquad
T_3=CQ_0C^T.
\tag{10}
\]

Their official FOCUS repository contains two similarly named assets, but only
`pyfocus/camps/file/clifford_2qubit_big.npz` at commit
`05b5b3a37a6dfcdfad1d809155f387565ed17734` is complete in the post-action-local direction. Its SHA-256 is
`466b03f9d2c59dcee5c67c9a97c348e5415b21c34b4a94b04b4fdb8aee996a8e`; it contains `clifford_ops (20,4,4)` and `tableau (20,4,4)` and has no `index` field. Independent orbit checking gives \(20\times36=720\).

The older `clifford-2bits-unique-entropy-big.npz` and its 20-index list are not suitable: they cover the input/pre-local direction, collapse to only 13 post-local classes, and cover only 468 post-local elements. That index list must not be copied. The correct asset is an external cross-check, not evaluator truth. The project reconstruction must independently:

1. enumerate \(G=\operatorname{Sp}(4,\mathbb F_2)\) and local \(H\);
2. define
   \[
   k(S)=\operatorname{lexmin}_{L\in H}\operatorname{flatten}(LS\bmod2);
   \tag{11}
   \]
3. verify 20 keys, orbit size 36, and \(20\times36=720\);
4. verify score invariance inside every post-local orbit;
5. compare the resulting canonical representatives with the pinned FOCUS asset up to convention.

For qutrits the same project algorithm over \(\mathbb F_3\) must yield 90 keys, orbit size 576, and \(90\times576=51840\). No authoritative public list of all 90 matrices or circuits was found. GCAMPS only describes enumeration, single-site canonicalization, and deduplication; it does not publish the list, key, tie-break, or stopping rule.

### L6 — exact-small objective versus scalable PEPS objective

For the exact-small course-project slice, freeze a family of physical bipartitions \(\mathcal E\) associated with the finite PEPS geometry and use an exactly contracted Rényi-2 score

\[
S_2(\rho_A)=-\log\operatorname{Tr}(\rho_A^2),
\qquad
J(Q)=\max_{e\in\mathcal E}S_2(\rho_{A_e}(Q\phi)),
\tag{12}
\]

with a registered sum-score and lexicographic candidate key as tie-breaks. Liu and Clark, arXiv:2412.17209v2, Sec. IV.A Eq. (19), use the equivalent purity objective in an MPS bond search. Qian et al., arXiv:2405.09217v2, instead minimize discarded SVD weight. Both are MPS methods; neither supplies a PEPS proof.

For a PEPS-specific compression score, the source-supported object is normalized whole-network fidelity. Evenbly, arXiv:1801.05390v2, Sec. V Eq. (12), optimizes a full-environment truncation using this fidelity. The alternating solve is not a global-convergence theorem, but the fidelity of any returned candidate remains an evaluable certificate when the finite network is contracted exactly.

The 20-candidate reduction is valid only if the chosen score is post-local invariant. Exact physical-cut entropy is invariant by construction. An approximate environment heuristic must demonstrate this invariance; otherwise it is not allowed to use the quotient as if it were exact.

### L7 — exact-small error accounting

Define trace distance

\[
D(\rho,\sigma)=\tfrac12\|\rho-\sigma\|_1.
\]

For normalized pure states with fidelity \(F\),

\[
D=\sqrt{1-F}.
\tag{13}
\]

For deterministic exact evolution interrupted by truncations whose exact whole-state fidelities are \(F_t\), a hybrid argument using CPTP contractivity gives the project theorem

\[
D_{\rm final}
\le
\min\left(1,\sum_t\sqrt{1-F_t}\right).
\tag{14}
\]

Consequently,

\[
|\operatorname{Tr}[O(\rho-\widetilde\rho)]|
\le 2\|O\|_\infty D_{\rm final},
\qquad
\operatorname{TV}(p_M,\widetilde p_M)\le D_{\rm final}.
\tag{15}
\]

For a complete enumerated classical–quantum frontier, if truncation \(t\) preserves the branch weights and has branchwise fidelity \(F_{t,h}\), its exact increment is bounded by

\[
\Delta_t
=\sum_h w_{t,h}\sqrt{1-F_{t,h}},
\qquad
\operatorname{TV}(P_{\rm raw},\widetilde P_{\rm raw})
\le\min\left(1,\sum_t\Delta_t\right).
\tag{16}
\]

A deterministic Record fold is a classical channel, so the same upper bound applies to the folded Record law. Equation (16) does not certify a rare normalized conditional branch; such branches require separate direct fidelity checks. Equations (14)–(16) are project derivations, not claims made by the PEPS papers.

If an approximate contraction independently certifies

\[
|a-\widehat a|\le\eta_a,
\quad |b-\widehat b|\le\eta_b,
\quad |c-\widehat c|\le\eta_c,
\]

for overlap \(a\) and norms \(b,c\), then

\[
F_{\rm lo}
=
\frac{\max(0,|\widehat a|-\eta_a)^2}
     {(\widehat b+\eta_b)(\widehat c+\eta_c)}
\tag{17}
\]

is a lower bound when the denominator bounds are positive. No generic method producing these \(\eta\) values for ordinary CTMRG/boundary approximations was found. General PEPS contraction is worst-case #P-complete (Schuch et al., PRL 98, 140506), so convergence in an environment bond dimension is not itself a certificate.

## 3. SDIM boundary and phase ledger

The inspected `events555/sdim` source is version 1.3.3 at commit
`115c495b23ade35ef0f68b7299afef463129bf51`. It strongly tests prime dimensions and warns that its fast composite solver can fail. It supplies prime-dimension tableau execution, not group enumeration or a 90-representative catalogue. It is not importable in the current `ecs` environment because required dependencies are absent; the current project seam is therefore fail-closed.

For a generalized Pauli word \((p,\mathbf x,\mathbf z)\) representing
\(\rho^pX^{\mathbf x}Z^{\mathbf z}\), let

\[
r=\begin{cases}d,&d\text{ odd},\\2d,&d\text{ even},\end{cases}
\qquad
\kappa=\begin{cases}1,&d\text{ odd},\\2,&d\text{ even}.
\end{cases}
\]

Here

\[
p,q\in\mathbb Z_r,\qquad
\mathbf x,\mathbf z,\mathbf u,\mathbf v\in\mathbb Z_d^n.
\]

In Eqs. (18)–(19), phase components are reduced modulo \(r\), exponent vectors are reduced componentwise modulo \(d\), and \(m\in\mathbb Z\).

Then the phase-aware operations required by GCAMPS Eq. (5) are

\[
(p,\mathbf x,\mathbf z)(q,\mathbf u,\mathbf v)
=
(p+q+\kappa\,\mathbf z\!\cdot\!\mathbf u,
 \mathbf x+\mathbf u,\mathbf z+\mathbf v),
\tag{18}
\]

and

\[
(p,\mathbf x,\mathbf z)^m
=
\left(mp+\kappa(\mathbf x\!\cdot\!\mathbf z)\frac{m(m-1)}2,
 m\mathbf x,m\mathbf z\right).
\tag{19}
\]

Hostens, Dehaene, and De Moor, quant-ph/0408190v2, Eqs. (4)–(10) and Appendix C, support the modular symplectic representation and phase conventions. With SDIM generators stored as columns,

\[
M=\begin{bmatrix}X_S&X_D\\Z_S&Z_D\end{bmatrix},
\qquad
M\begin{bmatrix}\mathbf s\\\mathbf d\end{bmatrix}
=
\begin{bmatrix}\mathbf x_P\\\mathbf z_P\end{bmatrix}\pmod d,
\tag{20}
\]

followed by ordered generator multiplication recovers the phase. Equation (20)
uses the SDIM decomposition-basis column order
`[stabilizers | destabilizers]`, so its coefficient vector is explicitly
`[s_Z-generators | d_X-generators]`. It is not the canonical Hostens Clifford
matrix. With Hostens coordinates \(a=(x,z)\), canonical input columns
`[X_i | Z_i]`, and SDIM's initial stabilizer \(Z_i\)/destabilizer \(X_i\), the
corresponding canonical symplectic matrix is instead

\[
C_{\rm Hostens}=
\begin{bmatrix}X_D&X_S\\ Z_D&Z_S\end{bmatrix}.
\tag{21}
\]

Confusing Eqs. (20) and (21) swaps the generator blocks and can reverse a
catalogue action convention. This generalized algebra must be a separate
prime-qudit layer. Merely changing `dimension=2` to 3 in the current Stim-typed
CAPEPS state would be incorrect. Composite dimensions remain blocked.

## 4. Disconfirmation surface

The closure deliberately keeps the following negative evidence:

- the double-sided 20-class statement in arXiv:2602.15942v2 fails on a fixed-input counterexample;
- the same paper proves that a universal exact Clifford disentangler of even one site exists only under stabilizer restrictions (Theorem III.1 and Appendix B);
- local Clifford sweeps can become trapped; Liu–Clark give an explicit heuristic failure example;
- Kim–Oh–Kim prove an AKLT-family result, not a generic PEPS optimum;
- Qian et al. only state that CAMPS can be extended to PEPS; they do not provide the PEPS objective, contraction, or certificate;
- Czarnik–Dziarmaga–Corboz, arXiv:1811.05497, use approximate CTMRG environments and numerical convergence, not a generic state/observable error bound;
- Werner et al., arXiv:1412.5746, provide a cumulative trace-norm bound for one-dimensional locally purified tensor networks and explicitly do not supply a 2D PEPS analogue;
- SDIM is a prime-qudit execution/cross-check backend, not the source of 90 representatives.

## 5. Evidence coverage, anomaly, and discovery ledgers

### 5.1 Coverage and admission ledger

`Inspected` means the versioned primary artifact and locator were checked. It
is not synonymous with admission to `CURRENT_CORPUS.toml`.

| Load-bearing row | Primary locator | Inspection result | Corpus/admission state |
|---|---|---|---|
| hybrid split, signed pullback, paired refactor | Harper et al., Secs. 2.3.1 and 3, Eq. (5), Fig. 3 | `CLOSED_SOURCE_FACT` | admitted current-corpus source; artifact-verified audit validated |
| qubit post-local quotient and 20-key construction | Chang et al., Eq. (10), Appendix Algorithms 1–2 and Theorem 1; pinned FOCUS commit | `CLOSED_DESIGN` | admitted current-corpus source; code audit is external differential only |
| qutrit post-local count 90 | Kim–Oh–Kim, Supplement Eqs. (S6)–(S7) | `CLOSED_COUNT_ONLY` | source note open |
| double-sided quotient disconfirmation | Masot-Llima et al., Sec. II.B; Córcoles et al., Supplement; explicit CNOT counterexample | `CLOSED_PROJECT_FALSIFIER` | both source notes open; counterexample is project derivation |
| exact-small purity/Rényi-2 objective | Liu–Clark, Sec. IV.A Eq. (19); Qian et al., Eqs. (4)–(5) | `CLOSED_DESIGN` | Liu–Clark admitted; Qian source note and repository metric registration open |
| exact finite-network fidelity | Evenbly, Sec. V Eq. (12) | `CLOSED_CONDITIONAL_CERTIFICATE` | admitted current-corpus source |
| generic PEPS contraction barrier | Schuch et al., main complexity theorem | `CLOSED_NO_GO_BOUNDARY` | admitted current-corpus source |
| conditional local-observable approximation | Schwarz–Buerschaper–Eisert, Theorem 1 and Eqs. (1), (5) | `CONDITIONAL_EXCEPTION` | source note open; requires injectivity, a uniformly gapped parent family, and condition-number control |
| variational iPEPS environment | Vanderstraeten et al., Sec. IV and Appendix B Eq. (B4) | `ALGORITHM_INDEPENDENT_SUBCLASS_ONLY` | source note open; no generic whole-state a posteriori bound |
| generalized Pauli phase algebra | Hostens et al., Eqs. (4)–(10), Appendix C; pinned SDIM source | `CLOSED_PRIME_QUDIT_ALGEBRA` | paper source note and executable isolated environment open |
| direct Clifford-frame + PEPS-residual precedent | admitted Harper hybrid-MPS source plus the discovery log below | `MISSING/OPEN_AFTER_DISCOVERY` | adjacent MPS precedent admitted; CAPEPS remains `[ours/proposed]` |

The admitted Evenbly and Schuch rows support only the stated PEPS fidelity and
complexity boundaries. They do not admit the unlisted hybrid-Clifford papers by
proxy.

### 5.2 Anomaly ledger

1. Masot-Llima et al. write a double-sided relation for the 20-class reduction.
   It fails for a generic fixed input: CNOT and
   CNOT\((H\otimes I)\) are related on the input side but map \(|00\rangle\)
   to states with different Rényi-2 entanglement.
2. FOCUS ships two similarly named 20-entry assets. Only
   `clifford_2qubit_big.npz` at commit `05b5b3a` covers all 720 elements in the
   post-action-local direction. The indexed legacy asset covers only 468 in
   that direction and must not be imported.
3. FOCUS contains a backward-sweep phase-index bug that is dormant for its
   zero-phase representatives. Its floating matrices and phase logic are not
   evaluator truth.
4. GCAMPS motivates qutrit enumeration but publishes neither the 90 matrices
   nor a canonical key. The catalogue must be independently generated.
5. Harper et al., arXiv:2605.29514v1, provide a directly relevant hybrid
   stabilizer–tensor-network QEC precedent, but Eq. (7) still uses an MPS
   residual. Their Sec. IV.B truncation validation is empirical convergence,
   not a PEPS whole-state certificate.
6. Vanderstraeten et al. make contraction algorithm-independent only for a
   symmetry-restricted iPEPS subclass; Schwarz et al. give a rigorous local
   observable error bound only under strong injective/gapped/conditioned
   assumptions. Neither closes the generic CAPEPS approximate-environment row.

### 5.3 External discovery log — not a close-literature search-exhaustion record

On 2026-07-27, after explicit user authorization, three five-query batches were
sent to AnySearch using the `academic.search` or `academic.preprint` vertical.
The exact query strings were:

Batch A — broad mechanism and certificate search:

1. `two-qubit Clifford one-sided local Clifford cosets 20 representatives entanglement optimization`
2. `two-qutrit Clifford local equivalence cosets 90 representatives`
3. `Clifford augmented tensor network PEPS disentangling hybrid stabilizer tensor network`
4. `projected entangled pair state exact finite network Renyi-2 Schmidt entropy local unitary disentangler`
5. `PEPS approximate contraction rigorous a posteriori error bound CTMRG fidelity certificate`

Batch B — named-paper and direct-precedent search:

1. `Classical simulation with Clifford-augmented matrix product states GCAMPS Harper`
2. `Clifford disentanglers tensor networks 20 90 Masot-Llima`
3. `FOCUS flexible optimization Clifford circuits quantum chemistry Chang local equivalence`
4. `two-qutrit Clifford 90 AKLT entanglement Kim Oh Kim`
5. `stabilizer tensor network PEPS hybrid Clifford residual exact simulation`

Batch C — deliberate disconfirmation search for a scalable PEPS certificate:

1. `PhysRevB 105 195140 PEPS variational contraction subclass algorithm independent`
2. `Approximating local observables on projected entangled pair states Schwarz Buerschaper Eisert theorem conditions`
3. `certified PEPS contraction error bounds local observables injective PEPS`
4. `variational boundary states projected entangled pair state contraction error bound`
5. `a posteriori tensor network contraction error estimate projected entangled pair states`

AnySearch results were treated as discovery pointers only. Target papers were
reopened at arXiv, publisher, or pinned repository sources. The searches found
GCAMPS, the qutrit AKLT work, CAGMPS, the surface-code hybrid MPS application,
Vanderstraeten's variational iPEPS subclass, and Schwarz's conditional
local-observable theorem. They did not produce an authoritative public
90-representative list, a direct Clifford-frame + PEPS-residual implementation,
or a generic a posteriori whole-state error certificate for ordinary
CTMRG/boundary contraction.

Because per-query candidates, dispositions, local RAG/KG retrieval queries, and citation-chain checks are not recorded here, this log does not satisfy the repository search-exhaustion contract. The affected absence rows remain `MISSING/OPEN`, not `confirmed-literature-gap`.

Within this dated discovery batch only, no returned candidate closed those rows. That observation is neither a field-wide absence claim nor proof that no such paper exists. A newly located primary source reopens the affected row.

## 6. Closure matrix and code gate

| Claim or implementation slice | Status | Consequence |
|---|---|---|
| exact untruncated frame/residual algebra | `CLOSED` | existing mechanics may remain |
| paired Clifford refactor preserves physical ray | `CLOSED` | optimizer choice affects efficiency, not exact semantics |
| qubit post-local quotient count 20 | `DESIGN_FROZEN__SOURCE_ADMITTED` | metric gate still blocks implementation |
| executable public qubit cross-check | `CLOSED_EXTERNAL_DIFFERENTIAL` | use pinned FOCUS only as an external differential |
| qutrit count 90 | `CLOSED_COUNT_ONLY` | self-enumeration and phase lift still required |
| public authoritative 90-representative list | `MISSING/OPEN` | do not hard-code an unattributed list |
| exact-small physical-cut entropy score | `DESIGN_CLOSED__METRIC_UNREGISTERED` | register owner and independent value test before code |
| exact finite-network whole-state fidelity | `CLOSED_FOR_CERTIFICATE` | may bound deterministic or complete-cq error under stated assumptions |
| scalable approximate PEPS environment certificate | `OPEN_GENERIC__CONDITIONAL_CLASSES_EXIST` | generic optimizer/compression target remains `CODE_BLOCKED` |
| direct prior Clifford-frame + PEPS-residual implementation | `MISSING/OPEN` | CAPEPS bridge must be labelled `[ours/proposed]` |
| SDIM prime-qutrit execution | `ENVIRONMENT_BLOCKED` | isolate environment and preregister separately |
| SDIM/composite-d correctness | `OPEN/NEGATIVE` | no composite support claim |

Theory-first design verdict:

- `EXACT_SMALL_QUBIT_DESIGN_FROZEN`: a 20-representative post-local catalogue, exact score differential, paired-refactor invariant, and exact finite-network certificate have been specified in a result-blind preregistration.
- `BLOCK_CODE_PENDING_METRIC_REGISTRATION`: the minimal exact-small source set is admitted, but the design verdict is not code permission; the repository metric-owner/value-test gate remains open.
- `BLOCK_SCALABLE_APPROXIMATE_PEPS`: no generic certified approximate environment was closed; do not implement or report a scalable correctness claim from CTMRG convergence alone.
- `BLOCK_QUTRIT_CAPEPS`: the 90 count and phase algebra are grounded, but the current residual/instrument is qubit-only and live SDIM is unavailable.

No `src/**` change is authorized by this packet. Repository policy still requires explicit user confirmation and a reviewed phase diff before implementation.

## 7. Primary sources and exact load-bearing locators

- Harper et al., [arXiv:2511.06672v2](https://arxiv.org/abs/2511.06672v2): Secs. 2.3.1 and 3, Eq. (5), Fig. 3, PDF pp. 4–6.
- Qian, Huang, and Qin, [arXiv:2405.09217v2](https://arxiv.org/abs/2405.09217v2): Fig. 1(b), Eqs. (4)–(5), Discussion, PDF pp. 2–4.
- Liu and Clark, [arXiv:2412.17209v2](https://arxiv.org/abs/2412.17209v2): Sec. IV.A Eq. (19), Appendix C, PDF pp. 9 and 25–26.
- Masot-Llima et al., [arXiv:2602.15942v2](https://arxiv.org/abs/2602.15942v2): Sec. II.B and Theorem III.1; Appendix B, PDF pp. 3, 6, 14–16.
- Chang et al., [arXiv:2606.12056v1](https://arxiv.org/abs/2606.12056v1): Eqs. (8)–(10), Appendix Algorithms 1–2 and Theorem 1, PDF pp. 4–5 and 13–15.
- Kim, Oh, and Kim, [arXiv:2607.03939v1](https://arxiv.org/abs/2607.03939v1): Supplement Eqs. (S6)–(S7), Table S2, Lemma 3, Theorem 1, PDF pp. 9 and 18–20.
- Hostens, Dehaene, and De Moor, [quant-ph/0408190v2](https://arxiv.org/abs/quant-ph/0408190v2): Eqs. (4)–(10), Secs. III–IV, Appendix C, PDF pp. 2–6 and 9.
- Li et al., [arXiv:2508.14670v1](https://arxiv.org/abs/2508.14670v1): Proposition 3.9, Corollary 3.10, Proposition 4.3, Theorem 4.4, Appendix B.3.
- Córcoles et al., [arXiv:1210.7011v2](https://arxiv.org/abs/1210.7011v2): Supplement, “Decomposition of the two-qubit Clifford operations.”
- Evenbly, [arXiv:1801.05390v2](https://arxiv.org/abs/1801.05390v2): Sec. V Eq. (12), PDF p. 6.
- Schuch et al., [Phys. Rev. Lett. 98, 140506](https://doi.org/10.1103/PhysRevLett.98.140506): PEPS contraction complexity.
- Czarnik, Dziarmaga, and Corboz, [arXiv:1811.05497](https://arxiv.org/abs/1811.05497): Eqs. (12)–(18), PDF pp. 4–5.
- Werner et al., [arXiv:1412.5746v2](https://arxiv.org/abs/1412.5746v2): Theorem 7 and Eqs. (60), (70)–(73), PDF pp. 11–12.
- Vanderstraeten et al., [arXiv:2110.12726v2](https://arxiv.org/abs/2110.12726v2): Sec. IV and Appendix B, especially Eq. (B4), PDF pp. 4–8 and 16.
- Schwarz, Buerschaper, and Eisert, [arXiv:1606.06301v2](https://arxiv.org/abs/1606.06301v2): Theorem 1 and Eqs. (1), (3)–(5), PDF pp. 2–4.
- Harper et al., [arXiv:2605.29514v1](https://arxiv.org/abs/2605.29514v1): Sec. IV, Eqs. (7)–(8), Figs. 2–3, PDF pp. 4–5.
- FOCUS code and correct 20-entry asset: [commit `05b5b3a`](https://github.com/Quantum-Chemistry-Group-BNU/FOCUS/commit/05b5b3a37a6dfcdfad1d809155f387565ed17734), with the asset loaded by `h_chain_sto3g_tets.py` lines 162–173.
- SDIM source: [events555/sdim at `115c495`](https://github.com/events555/sdim/tree/115c495b23ade35ef0f68b7299afef463129bf51).
