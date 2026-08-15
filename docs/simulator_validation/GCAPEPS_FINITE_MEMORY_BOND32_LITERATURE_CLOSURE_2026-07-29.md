# GCAPEPS finite-memory bond-32 benchmark — literature closure

Date: 2026-07-29

Status: **closed for a bounded project-defined persistent-memory unitary
dilation, exact-dense fixed-pair and registered finite-ensemble BLP witnesses,
and bounded carrier comparison; not closed for a generic non-Markovian QEC
Record, monotonic entanglement growth, or a universal GCAPEPS speedup**

## 1. Frozen scientific object

The benchmark keeps a finite memory register \(M\) inside the simulated state:

\[
|\Psi_r\rangle_{SM}
=U_rU_{r-1}\cdots U_1
\left(|\psi_0\rangle_S\otimes|0\cdots0\rangle_M\right).
\]

The same memory sites survive every round.  The reduced system trajectory is

\[
\rho_S(r)=\operatorname{Tr}_M
\left[|\Psi_r\rangle\langle\Psi_r|\right].
\]

This is a project-defined finite-dimensional persistent-memory unitary
dilation that Quimb can carry: the memory is represented by ordinary PEPS
sites and the state is not restarted between rounds.  It is not Campbell et
al.'s advancing-ancilla construction and it does not reproduce their
fixed-memory SWAP equivalence, which additionally requires fresh ancillas,
SWAPs, partial traces, and a stated collision schedule.  Audit of the pinned
local Quimb fork/source found no dedicated `non_markovian=True` semantic switch,
and none is required for the bounded project construction.

Memory retention is a mechanism, not by itself an operational diagnosis.  For
two registered system inputs evolved with the same initial memory state and
the same maps, define

\[
D_r=\frac12\left\|\rho_{S,1}(r)-\rho_{S,2}(r)\right\|_1,
\qquad
\mathcal N_{\rm pair}^{(R)}
=\sum_{r=1}^{R}\max(0,D_r-D_{r-1}).
\]

For the separately registered 32-mask ensemble, mask index is an unobserved
classical component of one common mixture map.  Both registered inputs use the
same input-independent weights, exactly `1/32`, and the reduced states are
averaged before trace distance:

\[
\bar\rho_{S,a}(r)=\frac1{32}\sum_{m=0}^{31}\rho_{S,a,m}(r),\qquad
\bar D_r=\frac12\left\|\bar\rho_{S,1}(r)-
\bar\rho_{S,2}(r)\right\|_1,
\]

\[
\bar{\mathcal N}_{\rm pair}^{(R)}=
\sum_{r=1}^{R}\max(0,\bar D_r-\bar D_{r-1}).
\]

Averaging pathwise distances, pathwise positive increments, or conditional
fixed-mask verdicts is a different object and is forbidden.  The finite-
ensemble witness is therefore the registered mixture-map witness for this one
input pair, not an ensemble of conditional witness votes and not the optimized
BLP measure.

An exact-dense increment greater than the registered \(10^{-10}\) threshold is
the bounded BLP non-Markovian witness.  The experiment does not optimize over
every input pair, so \(\mathcal N_{\rm pair}^{(R)}\) is not the full BLP
measure.  If no fixed-mask increment crosses the threshold, the exact verdict
is `NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR`; for the separately registered
finite ensemble it is `NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR`.
Neither verdict is proof of Markovianity.

## 2. Collision primitive and project-defined axis families

Campbell et al. use the pair Hamiltonian

\[
H_{ij}=-\frac12
\left(J_xX_iX_j+J_yY_iY_j+J_zZ_iZ_j\right).
\]

Campbell Eq. (2) together with its Eqs. (3)--(4), which use
\(e^{-iH_{ij}\tau}\), algebraically gives the positive-sign partial SWAP up to
a global phase.  The paragraph immediately after Eq. (4) instead prints a
negative-sign partial SWAP.  This internal source inconsistency is recorded in
`CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_2026-07-29.md`.
The project does not use that negative-sign sentence.  Its executable
collision primitive is independently frozen from McCloskey--Paternostro
Eq. (1):

\[
U_{\rm MP}(\gamma)=\cos\gamma I+i\sin\gamma\,\mathrm{SWAP}.
\]

Campbell Eq. (2) supplies only the pair-interaction coordinates.  The project
freezes three axis families; these labels are not a source-defined monotonic
complexity ordering:

\[
\begin{array}{c|ccc}
\text{axis family}&J_x&J_y&J_z\\
\hline
1&0&0&J\\
2&J&J&0\\
3&J&J&J
\end{array}
\]

using the rotation convention

\[
R_{PP}(\theta)=\exp(-i\theta P\otimes P/2),
\qquad \theta=-\gamma.
\]

For axis family 3, the Pauli products commute and

\[
\mathrm{SWAP}=\frac12(I+XX+YY+ZZ),
\]

so

\[
\cos\gamma I+i\sin\gamma\,\mathrm{SWAP}
=e^{i\gamma\,\mathrm{SWAP}}
=e^{i\gamma/2}
 e^{i\gamma XX/2}
 e^{i\gamma YY/2}
 e^{i\gamma ZZ/2}.
\]

The displayed adjacency denotes an operator product.  If
\(U_{\rm rot}=R_{XX}(-\gamma)R_{YY}(-\gamma)R_{ZZ}(-\gamma)\), then the frozen
direction of the phase identity is
\(U_{\rm rot}=e^{-i\gamma/2}U_{\rm pswap}\).  An independent untimed matrix
control must verify the sign, product, order independence, and global-phase
firewall before any target run.  Once a candidate truncates between axes, its
three approximate updates are not re-described as one exact partial-SWAP.

At each registered system–memory location and round, a project-defined
hash-threshold mask either includes or omits the complete collision.  The
source supplies only a draw-and-threshold precedent; it does not specify the
draw distribution or identify its threshold with a Bernoulli probability.
The project therefore defines its own uniform-hash schedule and a finite,
equally weighted mask ensemble.  For a fixed mask, \(p_{\rm event}\) is a
schedule-generation coordinate, not an observed frequency.  For the registered
finite ensemble it is the inclusion threshold, not a calibrated device error
rate or Pauli-twirl probability.  Realized counts and fractions are always
reported.

## 3. Coverage ledger

| load-bearing row | required object | source and exact locator | status | experiment consequence |
|---|---|---|---|---|
| reduced-state distinguishability | trace distance between two system states | Breuer–Laine–Piilo, Eq. (1), PDF p. 1; `breuer_laine_piilo_nonmarkovianity_0908.0238v2_source_review.md` | closed | compute the trace norm of independently reduced dense states |
| positive-backflow witness | positive trace-distance derivative/increments for one common map | Breuer–Laine–Piilo, Eqs. (10)–(12), PDF pp. 2–3 | closed | any positive exact-dense increment witnesses the registered non-Markovian trajectory; no revival is inconclusive |
| finite-bath nonmonotonicity | finite memory can exchange information back and forth | Breuer–Laine–Piilo, Eq. (14), PDF p. 4 | closed | oscillation and revival are allowed; monotonic entanglement is not a premise |
| coherent collision and retained correlations | partial-SWAP system–ancilla and ancilla–ancilla collisions; early erase versus retain | McCloskey–Paternostro, Eqs. (1)–(4), (10)–(11), PDF pp. 2, 4 | closed | explicit memory retention is a defensible mechanism |
| stochastic collision occurrence | source draw-and-threshold rule; project uniform-hash distribution | McCloskey–Paternostro, Sec. II.B and Fig. 6, PDF p. 6 | source rule closed; probability bridge project-defined | bind one carrier mask across candidate/reference lanes and a separate finite dense ensemble |
| finite-memory embedding boundary | advancing \(d=1,2\) enlarged states; separate fixed-memory SWAP equivalence and schedule | Campbell et al., Eqs. (7)–(13), PDF p. 5; Eqs. (14)–(18) and timing qualification, PDF pp. 6–7 | closed as adjacent source, not project equivalence | call the closed ladder a project-defined dilation and diagnose reduced \(S\) independently |
| pair Hamiltonian / collision sign / project axis families | \(XX+YY+ZZ\) coordinates and a positive-sign partial-SWAP primitive | Campbell et al., Eq. (2), Eqs. (3)–(4), and post-Eq. (4) sentence, PDF p. 2; McCloskey–Paternostro Eq. (1), PDF p. 2; `CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_2026-07-29.md` | operator coordinates and McCloskey unitary closed; Campbell internal sign bridge rejected; family taxonomy project-defined | use the McCloskey positive branch, freeze \(\theta=-\gamma\), and sweep families 1–3 without claiming a literature-defined complexity order |
| Clifford-frame residual | \(|\psi\rangle=C|\mathrm{TN}\rangle\) and Pauli pull-through | Harper et al., Sec. IV.A, Eq. (7), PDF p. 4; admitted source review | closed adjacent; published carrier is MPS | the PEPS extension remains a project implementation, not a paper claim |
| complete-state error | normalized squared whole-state overlap | Evenbly, Sec. V, Eq. (12), PDF p. 6; admitted source review | closed | materialize the bounded complete vector and compare with an independent dense vector |
| local truncation diagnostic | local retained/discarded spectra are not a generic whole-state certificate | Rudolph–Tindall, Sec. II, Eqs. (1)–(2), PDF p. 3; Evenbly loop/gauge limitations | closed limitation | report positive discarded weight as causal evidence only; fidelity remains independent |
| generic contraction boundary | exact PEPS primitives/general TN contraction have `#P` hardness in the source setting | Schuch et al., VOR PDF pp. 2–3; admitted source review | no-go boundary | no scalable contraction or generic efficiency conclusion follows |
| timing and memory | wall time, CPU time, RSS, tensor elements, and process launch time | project engineering definitions | closed by explicit instrumentation | values are class-(c) implementation measurements, not literature facts |

The three primary-source audits and one cross-source audit are:

- `BLP_0908_0238V2_NONMARKOVIAN_WITNESS_AUDIT_2026-07-29.md`;
- `MCCLOSKEY_PATERNOSTRO_1402_4639V3_COLLISION_AUDIT_2026-07-29.md`;
- `CAMPBELL_1805_09626V2_MEMORY_DEPTH_AUDIT_2026-07-29.md`;
- `CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_2026-07-29.md`.

Independent source admission is bound by:

- `BLP_MCCLOSKEY_NONMARKOVIAN_INDEPENDENT_SOURCE_REREVIEW_ROUND3_2026-07-29.md`;
- `CAMPBELL_1805_09626V2_INDEPENDENT_SOURCE_REVIEW_ROUND2_2026-07-29.md`;
- `CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_INDEPENDENT_REVIEW_2026-07-29.md`,
  SHA-256
  `5a82ef698e57b800406ae7aff731af676e88b65205e20238a21bdff996c63963`;
- the artifact-verified 47-note corpus manifest rebuilt after admission.

## 4. Anomaly and disconfirmation ledger

| anomaly / competing explanation | evidence | disposition |
|---|---|---|
| McCloskey–Paternostro Eq. (8) prints an identically zero self-distance and omits the positive-increment selector used by Eq. (7). | visual check of Eq. (8), PDF p. 3; independent Round-3 review | do not implement it; use the separately labelled discrete derivation from BLP Eqs. (10)–(12), and require literal-Eq.-(8) and unrestricted-telescoping corruptions to fail |
| A persistent environment can exist without the registered input pair showing a revival. | BLP maximization and Campbell Eq. (5) discussion | distinguish mechanism from witness; zero is inconclusive |
| Campbell Eq. (2) plus Eqs. (3)–(4) imply a positive-sign isotropic partial SWAP up to global phase, while the post-Eq. (4) sentence prints the negative sign. | visual checks of Campbell PDF p. 2 and McCloskey–Paternostro Eq. (1), PDF p. 2; cross-source algebra audit | freeze the McCloskey positive-sign primitive, use Campbell only for coupling coordinates and adjacent memory context, and require an opposite-sign corruption to fail |
| Candidate truncation can create a false trace-distance revival. | mechanism-to-observable audit | compute the headline witness with an independent dense route; candidate witness error is secondary |
| System–memory entanglement can rise, fall, and revive. | BLP finite-spin-bath oscillation; McCloskey Figs. 3–6; external disconfirmation search | register monotonic growth only as a falsifiable project hypothesis |
| A larger PEPS bond or smaller local tail need not determine whole-state fidelity on a loopy network. | Evenbly and Rudolph–Tindall | require complete-vector fidelity at the bounded widths |
| Ordinary PEPS bond and GCAPEPS residual bond do not represent the same resource. | hybrid-state definition | compare each as carrier pressure; use exact \(S|M\) entropy as the common physical entanglement observable |
| GCAPEPS may save residual bond yet lose wall-clock time to routing, ledgers, copies, or validation. | project implementation surface | report algorithm-only and evidence-inclusive timing separately; no speedup is presumed |
| Exact-tree PEPO lowering currently performs no truncation. | audited fork implementation | the experiment requires a new opt-in exact-tree-then-native-compression path; setting `max_bond=32` alone is not evidence |

## 5. AnySearch external acquisition and disconfirmation log

Backend: AnySearch `academic.search`, domain schema obtained with
`get_sub_domains --domain academic`, 2026-07-29 UTC.  Queries contained no
local paths, code, unpublished values, or private data.

| exact query | relevant discovery | disposition |
|---|---|---|
| `finite memory collision model tensor network non-Markovian entanglement bond dimension rounds` | *Spatiotemporal Pauli processes: Quantum combs for modelling correlated noise in quantum error correction* | adjacent twirled process/comb representation; not a joint pure-state PEPS fidelity or carrier-speed premise |
| `non-Markovian collision model trace distance revival persistent ancilla partial swap` | collision-model applications and surveys | no replacement for the already full-text-reviewed BLP/McCloskey/Campbell mechanism and witness sources |
| `tensor network simulation non-Markovian open quantum dynamics explicit environment finite memory PEPS` | general tensor-network anthology and unrelated mixed-state work | no source found that supplies a generic PEPS truncation certificate for this experiment |
| `non-Markovian dynamics monotonic entanglement growth counterexample finite environment` | *Rise and fall of entanglement between two qubits in a non-Markovian bath* | disconfirmation discovery; no monotonic-growth premise is retained, and the abstract is not used to close a row |
| `Clifford augmented tensor network non-Markovian PEPS memory simulation` | Harper hybrid stabilizer–TN work and spatiotemporal Pauli processes | adjacent methods only; neither establishes the new GCAPEPS finite-memory implementation or a speedup |
| `quantum collision model Bernoulli random collisions probability partial swap non-Markovian` | adjacent stochastic/composite collision work | no full-text primary source found that closes the project's Bernoulli-presence distribution |
| `finite memory collision model fixed memory ancilla repeated interactions fresh ancillas swap non-Markovian` | Campbell-style fresh-ancilla/SWAP constructions | confirms adjacency and the non-equivalence of the closed ladder |
| `"stochastic collisions" non-Markovian quantum collision model probability` | stochastic collision discussions | snippets do not specify the missing source distribution and close no row |
| `quantum collision model random interaction occurs with probability p ancilla` | adjacent randomized collision models | no acquired primary source replaces the explicit project-design boundary |
| `quantum collision model reusable memory ancilla fresh ancillas swap memory depth` | persistent auxiliaries plus fresh reservoirs | not equivalent to a permanently closed \(2\times w\) ladder |
| `"Composite quantum collision models" Ciccarello Lorenzo Giovannetti Palma` | persistent auxiliary/fresh-reservoir abstract | adjacent only; abstract evidence closes no row |
| `tensor network non-Markovian open quantum dynamics explicit memory environment PEPS` | process-tensor/TEMPO papers and tensor-network reviews | supports the broader representation landscape only; no result is imported as a PEPS truncation certificate or Quimb API claim |
| `collision model non-Markovian memory ancilla partial swap quantum system` | McCloskey/Campbell collision-model family and adjacent reviews | routes back to the already admitted primary PDFs; no new distributional bridge is inferred |
| `Breuer Laine Piilo trace distance information backflow non-Markovianity` | BLP primary paper and subsequent reviews | routes back to the admitted equation-level BLP source; snippets close no additional row |
| `projected entangled pair states open system dynamics non-Markovian` | open-system tensor-network and process-tensor work | establishes adjacency, not a dedicated Quimb non-Markovian implementation or general PEPS efficiency result |
| `process tensor matrix product state finite memory non-Markovian quantum dynamics` | Pollock et al., TEMPO, and causal process-tensor algorithms | alternative temporal-TN formulations; not equivalent to the closed two-row spatial carrier |
| `PEPS gate_simple_ simple update max_bond cutoff non-Markovian open quantum system` plus repository-scoped `gate_simple_ PEPS max_bond cutoff` | Quimb simple-update code/docs and an unrelated PEPO-circuit pull request | AnySearch found native PEPS split/update surfaces but no dedicated non-Markovian switch; the actual carrier/API boundary is verified from the pinned local source, not from search absence |
| `process tensor matrix product operator finite memory non-Markovian quantum dynamics tensor network` | Pollock process-tensor framework, TEMPO, and causal tensor-network algorithms | supports an explicit temporal many-body/MPO representation in bounded settings; it does not make the spatial ladder equivalent to a process tensor or certify PEPS contraction |
| `collision model partial swap finite memory non-Markovian quantum dynamics repeated interactions ancilla` | collision-model primary sources and adjacent finite-memory reviews | corroborates the retained-memory mechanism; the frozen unitary, sign, schedule, and witness still come only from the admitted full-text sources |
| `non-Markovian quantum dynamics tensor network process tensor matrix product state` | TEMPO/process-tensor and open-system tensor-network papers | confirms that tensor networks can carry memory, not that Quimb supplies a turnkey non-Markovian/process-tensor API or that bond must grow monotonically with rounds |
| `Markovian embedding non-Markovian quantum dynamics collision model memory depth Campbell 2018` and exact McCloskey-title query | the two already acquired primary collision-model sources | confirms source discovery and non-equivalence boundary; equation claims remain based on full-text audits |
| `Quimb non-Markovian open quantum dynamics tensor network implementation` | SpinPulse and process-tensor/influence-functional work | SpinPulse supplies its own classical colored-noise process and uses Quimb as an MPS numerical backend; this is an adjacent engineering precedent for separating model semantics from a Quimb carrier, not validation of this project's adaptor or evidence of a native Quimb non-Markovian semantic layer |
| `process tensor TEMPO finite memory tensor network non-Markovian dynamics` | Pollock causal process tensor, TEMPO, OQuPy, and finite-memory TN algorithms | establishes alternative temporal-memory TN constructions; none is identified with the preregistered closed spatial ladder, and none certifies its PEPS truncation |
| `collision model repeated ancilla environmental memory non-Markovian quantum dynamics` | Campbell-style Markovian embeddings and collision-model literature | supports explicit retained-memory/ancilla interaction as a non-Markovian mechanism; exact schedule, event law, and finite ladder remain project design |
| `non-Markovian dynamics monotonic entanglement bond dimension tensor network rounds` | search found no source supporting a universal monotonic implication; influence-functional work reports correlations that can increase and then decrease, consistent with the admitted finite-bath/collision counterexamples | supplies no support for a monotonic bond/entanglement premise; the complete trajectory is measured and any terminal increase is only the preregistered bounded-cell hypothesis |

Search snippets and abstracts close no row.  The three versioned primary PDFs
were acquired, read in full, independently rereviewed, and admitted.  Existing
admitted PEPS/GCAMPS sources close the carrier, fidelity, truncation-limitation,
and generic-complexity-boundary rows.

## 6. Closure verdict

```text
closure_status = closed
pass_to_prereg = yes
pass_to_code = conditional, only after a passing independent preregistration rereview and theory-only commit
scientific_object = project-defined finite-dimensional persistent-memory unitary dilation
non_markovian_claim = allowed only when the corresponding independent dense fixed-mask or finite-ensemble BLP witness is positive
collision_sign_claim = McCloskey positive-sign branch; Campbell post-Eq.-(4) negative-sign sentence excluded
monotonic_entanglement_claim = forbidden as a premise; allowed as a preregistered hypothesis
generic_speedup_claim = forbidden
generic_peps_faithfulness_claim = forbidden
campbell_embedding_equivalence_claim = forbidden
qec_record_claim = forbidden
measurement_reset_claim = forbidden
```

The downstream implementation may answer only the bounded questions:

1. whether the registered fixed schedule and separately defined finite mask
   ensemble show an exact-dense BLP revival;
2. how physical system–memory entanglement changes across the registered
   rounds;
3. how ordinary Quimb PEPS and tree-routed GCAPEPS differ at `max_bond=32` in
   complete-state error, candidate bond pressure, local truncation events,
   runtime, and memory; and
4. whether those observations survive the preregistered corruption and
   provenance gates.

