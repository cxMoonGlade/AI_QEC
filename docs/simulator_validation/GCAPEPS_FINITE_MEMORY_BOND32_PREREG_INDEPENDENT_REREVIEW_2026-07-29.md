# GCAPEPS finite-memory bond-32 preregistration — independent final rereview

Date: 2026-07-29

Verdict: **PASS_TO_THEORY_ONLY_COMMIT**

Severity count at the exact reviewed hashes:

```text
P0 = 0
P1 = 0
```

This is a source-, theory-, and preregistration-only review. No GCAPEPS
finite-memory target result, calibration result, held-out result, target
amendment, implementation patch, or experimental raw artifact was inspected.
The final reviewer changed only this rereview file. The owning session repaired
the literature closure and protocol documents in response to three independent
P1 findings before the final hashes below were bound.

This verdict authorizes only a theory-only commit containing the exact reviewed
packet and this rereview. It is not a pass-to-code, implementation acceptance,
or scientific result.

## 1. Exact reviewed object

Every value in this section is a complete-file SHA-256 computed from the
current workspace bytes immediately before this final rereview was written.

### 1.1 Theory and protocol packet

| artifact | complete-file SHA-256 |
|---|---|
| `docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_LITERATURE_CLOSURE_2026-07-29.md` | `d1b94b7745b16675d847da5c94d7e3e267354c8e5a71a7669574a2b4de5573d9` |
| `docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_PREREG_2026-07-29.md` | `eaaed221cd65f0517ecf816bfcda252b134d2fe36a9d9f9c88e5b22fc8519278` |
| `docs/METRICS.md` | `c21b68f5badef20e30e080920b2d2d38864cc9dafc8613552577eddce0ff802f` |
| `docs/NUMERICAL_PROVENANCE.md` | `fe0f8fc2ecd4d3e581d7f7aa6e695322643453e4ab92cf0e7a12c53444e95cd8` |
| `docs/papers/CURRENT_CORPUS.toml` | `92f2641418b8d0c315c5f4fa862319712d72555d8e0a87a87e3945508917c7a1` |

The manifest separately records canonical corpus identity
`d4f56873bd176ec182b446012d68d647118516548c24400da686b8298580defe`,
with 47 admitted notes and 699 paper facts. That internal set identity is not
substituted for the complete-file hash.

### 1.2 Three primary source reviews and fixed PDFs

| artifact | complete-file SHA-256 |
|---|---|
| `docs/papers/reading_notes/breuer_laine_piilo_nonmarkovianity_0908.0238v2_source_review.md` | `50c3eb8d8bd9db226e8a7f1b216ae4e5363353891cac9a3aae9c76c6cf842de6` |
| `docs/papers/reading_notes/campbell_markovian_embedding_1805.09626v2_source_review.md` | `23f0dfb5efe0913f8fff5eb340895ec6a2c1960abddc83fd586c12cc098ba3c3` |
| `docs/papers/reading_notes/mccloskey_paternostro_collision_1402.4639v3_source_review.md` | `7ac36da1ef52995c5737eb7d0e50767a1fc902dcbc83812bef1150e470927984` |
| `docs/papers/0908.0238v2.pdf` | `9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553` |
| `docs/papers/1805.09626v2.pdf` | `619f3a5fe047481ef1fc434255e63e0ca3428ca594805a34d9897ec0e9fb4fd5` |
| `docs/papers/1402.4639v3.pdf` | `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` |

### 1.3 Equation audits and independent admissions

| artifact | complete-file SHA-256 |
|---|---|
| `docs/simulator_validation/BLP_0908_0238V2_NONMARKOVIAN_WITNESS_AUDIT_2026-07-29.md` | `4151228066fc7e6e195c43debc3435dce7484b8169ab46352adfd356a2fa6b19` |
| `docs/simulator_validation/MCCLOSKEY_PATERNOSTRO_1402_4639V3_COLLISION_AUDIT_2026-07-29.md` | `4b28940ef532ff180f1e83a558ab5db3bee8de142b8283e17117712bb548577e` |
| `docs/simulator_validation/CAMPBELL_1805_09626V2_MEMORY_DEPTH_AUDIT_2026-07-29.md` | `364ca4438a1d8ddabb06c87cf54e36499cc93c3414afdc11a438a7b3016e1916` |
| `docs/simulator_validation/BLP_MCCLOSKEY_NONMARKOVIAN_INDEPENDENT_SOURCE_REREVIEW_ROUND3_2026-07-29.md` | `2c7760b6bd35d0f4f93a45dcf010d780b9208d0989e1c364de685f34ef0d55b8` |
| `docs/simulator_validation/CAMPBELL_1805_09626V2_INDEPENDENT_SOURCE_REVIEW_ROUND2_2026-07-29.md` | `e7afa993624f35e196801e9cae2b3e5c28397dc461700713f998d07d0faf76a6` |
| `docs/simulator_validation/CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_2026-07-29.md` | `c03915a4f91aae7c5c746871120ca2d9d904fbcaaac2a8a78d9de236899dc1a0` |
| `docs/simulator_validation/CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_INDEPENDENT_REVIEW_2026-07-29.md` | `5a82ef698e57b800406ae7aff731af676e88b65205e20238a21bdff996c63963` |

The admission-only note hashes in `CURRENT_CORPUS.toml` are the post-review
shadow hashes reported by the independent source reviews. No pre-admission
candidate hash is treated as a current admitted note.

## 2. Independent findings and their closure

The first rereview was not accepted as a gate because it found three P1
problems. The owning session repaired them, and two un-led reviewers then
performed incremental rereviews against the repaired bytes.

### 2.1 Finite-ensemble BLP construction

The literature closure previously named a registered finite-ensemble witness
without freezing the aggregation order. That was load-bearing because trace
distance is nonlinear.

The current closure now defines the mask as an unobserved classical component
of one mixture map and fixes identical, input-independent weights:

\[
\bar\rho_{S,a}(r)=\frac1{32}\sum_{m=0}^{31}\rho_{S,a,m}(r),
\qquad
\bar D_r=\frac12\left\|\bar\rho_{S,1}(r)-\bar\rho_{S,2}(r)\right\|_1,
\]

\[
\bar{\mathcal N}_{\rm pair}^{(R)}
=\sum_{r=1}^{R}\max(0,\bar D_r-\bar D_{r-1}).
\]

It expressly forbids averaging pathwise distances, pathwise positive
increments, or conditional fixed-mask witness votes. The object remains one
registered input-pair witness, not the pair-optimized BLP measure. The
literature reviewer independently rechecked this repair against the
preregistration, `METRICS.md`, and the BLP common-map boundary and returned
PASS with no P0/P1.

### 2.2 Worker working-directory contract

The protocol previously used wording that could be read as requiring a fresh
private working directory while also freezing exact
`WorkingDirectory=<repo_abs>`.

The current protocol requires a fresh private process/mount namespace while
using the exact read-only `WorkingDirectory=<repo_abs>`. This removes the
candidate/acceptance ambiguity without weakening repository or output-root
isolation. The protocol reviewer independently replayed the relevant clauses
and returned PASS.

### 2.3 Single serialization leaf

The protocol previously risked contradicting itself by appearing to serialize
the no-shadow carrier before the instrumented replay while also requiring one
serialization leaf after that replay.

The current packet freezes only base scalar, ledger, transcript, and final
carrier-hash values in memory, then releases the no-shadow carrier without
constructing core bytes. Only after the complete instrumented replay does the
single serialization leaf construct canonical `ndarray-v1` core bytes.
`evidence_worker_total` and `R_evidence` still include both trajectories and
that one final serialization. The protocol reviewer found no remaining stale
pre-replay serialization wording and returned PASS.

The final severity count is therefore P0 = 0 and P1 = 0, rather than a waiver
of the original findings.

## 3. Frozen question and claim boundary

The packet asks only whether a bounded, project-defined, pure-state
system--memory ladder can:

1. exhibit an independently computed fixed-pair or registered finite-mixture
   BLP trace-distance revival;
2. show the preregistered terminal-versus-first-round system--memory entropy
   direction at one held-out stress cell;
3. compare ordinary Quimb PEPS and tree-routed GCAPEPS at `max_bond=32`
   against an independent complete dense state; and
4. report bounded implementation timing and memory under named scopes.

It does not claim:

- a generic non-Markovian QEC Record;
- measurement/reset/instrument closure;
- Campbell-model equivalence;
- monotonic entanglement growth with round count;
- generic PEPS contraction or truncation certificates;
- a universal GCAPEPS speedup;
- asymptotic small bond;
- qutrit, composite-\(d\), or leakage correctness; or
- SDIM as state-level truth.

The reusable output is the frozen mechanism, metric, firewall, and control
protocol. It is not a general non-Markovian PEPS theorem.

## 4. Scientific mechanism and observable

### 4.1 Common-map BLP witness

The load-bearing source chain supports

\[
D(\rho_1,\rho_2)=\frac12\operatorname{Tr}|\rho_1-\rho_2|
\]

from BLP Eq. (1), and positive trace-distance rate/positive intervals from BLP
Eqs. (10)--(12). The registered sampled object

\[
\mathcal N_{\rm pair}^{(R)}
=\sum_{r=1}^{R}\max(0,D_r-D_{r-1})
\]

is correctly labelled a discrete fixed-pair lower-bound witness.

Both initial system states use the same initial memory, event mask, gate order,
and unitary parameters. Each checkpoint is therefore one common CPTP map
applied to both inputs. For the separately registered 32-mask object, the
states are mixed before distance as fixed in Section 2.1. A null is reported as
`NO_WITNESS_*_FOR_REGISTERED_PAIR`; it is never promoted to proof of
Markovianity.

McCloskey--Paternostro Eq. (8) is not used as executable truth. Its
self-distance defect and missing positive-increment selector remain explicit
corruption targets.

### 4.2 Persistent finite memory

The mechanism is accurately named a project-defined finite-dimensional
persistent-memory unitary dilation. The same memory sites remain inside the
state across rounds and are traced only by the independent reduced-state
calculation. This supplies a memory-carrying mechanism but is not itself a
non-Markovianity witness.

Campbell is used only as adjacent collision-model and coupling-coordinate
context. The packet explicitly does not claim the fresh-ancilla, swap,
partial-trace, advancing-label, and schedule equivalence of Campbell
Eqs. (14)--(18). One-, two-, and three-axis families are project categories,
not a literature-defined complexity hierarchy.

### 4.3 Collision sign

The packet preserves rather than hides the Campbell sign inconsistency.
Campbell Eq. (2) plus \(e^{-iH\tau}\) implies the positive partial-SWAP branch
up to global phase, while the sentence after Campbell Eq. (4) prints the
negative branch. The executable project primitive is instead the independently
printed McCloskey operator

\[
U_{\rm MP}(\gamma)=\cos\gamma I+i\sin\gamma\,\mathrm{SWAP}.
\]

Using

\[
\mathrm{SWAP}=\frac12(I+XX+YY+ZZ),
\qquad
R_{PP}(\theta)=e^{-i\theta PP/2},
\]

the frozen identity is

\[
R_{XX}(-\gamma)R_{YY}(-\gamma)R_{ZZ}(-\gamma)
=e^{-i\gamma/2}U_{\rm MP}(\gamma).
\]

The phase is analytic rather than fitted; all six factor orders must agree;
opposite-sign, sum-for-product, and missing-phase corruptions must fail. Axis
families 1 and 2 are not relabelled partial SWAPs.

## 5. Faithfulness and metric bridge

The candidate result is compared with an independently evolved dense
`complex128` vector. The reference hand-constructs the frozen matrices and
does not import Quimb, Stim, SDIM, GCAPEPS, or ECS. At the largest registered
width the complete state has \(2^{14}\) components, so the dense reference is
feasible rather than a proxy.

Whole-state fidelity is

\[
F(x,y)=
\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle},
\]

after independent shape, dtype, finiteness, and norm gates. Raw and normalized
\(d_2/d_\infty\), norm error, pure-state trace distance, reduced-state trace
distance, entropy error, resource pressure, local spectra, and discarded tails
remain separately named.

A local SVD tail is cause evidence for a registered truncation event only. It
is not a complete-state error certificate. Sparse candidate checkpoints are
never summed into BLP evidence. Candidate BLP values cannot replace the dense
witness. No generic PEPS contraction, accumulated truncation, or post-truncation
Record guarantee is inferred.

The entropy and faithfulness directions \(H_E\) and \(H_F\) are class-(b)
bounded project predictions. The \(10^{-10}\) witness/tie/tail decisions and
timing bands are class-(c) protocol thresholds. Timing and memory are
engineering measurements, not physics evidence.

## 6. Independent truth and evaluator firewall

The terminal comparator reconstructs claim-bearing metrics from raw canonical
bytes and imports none of the candidate or corroboration backends. Candidate
workers receive no dense state, dense scalar, peer-candidate value, SDIM
result, comparator value, path, hash, locator, or auxiliary descriptor.

Calibration can select only the first displayed parameter pair meeting the
registered Stage-D conditions. It may inspect witness and cap eligibility, not
fidelity. A separately committed amendment freezes the held-out object and
seed before target execution. Calibration artifacts cannot enter held-out
summaries.

The system-manager protocol gives workers distinct identities, read-only
repository access, an inaccessible output root, sealed raw-file input, and the
exact read-only repository working directory inside a private process/mount
namespace. The root runner is non-dumpable. Preflight and corruption tests
must deny output-root access, runner `/proc` handles, ptrace, and
`process_vm_readv`.

Input bytes are bound to externally owned complete-file hashes, fsynced,
reopened, reparsed, and carried in the final node identity. The repaired
single-serialization ownership described in Section 2.3 prevents a hidden
second evidence byte stream.

## 7. Controls, falsifiers, and performance scope

The \(p_{\rm event}=0\) control is analytically non-degenerate. With no
cross-row collision, system and memory remain a product, so system--memory
entropy is zero. Both system inputs undergo the same system-only unitary, so
their orthogonality and trace distance one are preserved. The protocol
therefore requires structural-zero event/rotation counts,
\(S_1,S_2\le10^{-12}\), \(|D_r-1|\le10^{-12}\), and no named positive
increment.

Before target selection, independent dense evidence must show a positive BLP
increment and all four plain/GC-by-input positive cap events. Full evidence
must reproduce them. A no-op memory knob, no-cap lane, or probe/full mismatch
cannot qualify.

The 40 registered corruption families cover the BLP equation defect,
partial-SWAP sign/product/phase, common-map and mask equality, memory reset,
input preparation, candidate/reference independence, state coordinates and
dtypes, complete metric formulas, split cause/pre-state, construction epochs,
refactor accounting, frame/pullback coverage, timing ownership, censor
precedence, publication identity, and process isolation. Every named
corruption must fail.

Performance claims remain bounded to the measured implementation:

- `candidate_algorithm_case_e2e` includes all algorithm updates, routing,
  validation, copies, and commits required by that lane;
- reference/evidence/materialization and serialization work remain separately
  named;
- worker wall, main-process CPU, service-launch wall, workflow wall, cgroup
  CPU, RSS, peak memory, and logical tensor bytes are not conflated;
- all three measured samples, fixed launch order, raw values, median, unscaled
  MAD, and same-direction GC/plain ratios are required; and
- censoring makes a ratio unavailable rather than changing the population.

No generic or asymptotic runtime advantage is predicted.

## 8. SDIM boundary

SDIM 1.3.3 is a qubit-only Clifford-frame corroboration lane. It is not a
state oracle. Its installed-state inventory is externally hashed and cannot
self-bind or be regenerated between calibration and held out.

The neutral fixture owns the pullback requests. SDIM and a separately
constructed Stim replay receive no GC values. SDIM must first establish exact
ordered \(E=S=T\); the comparator separately requires unique equal-cardinality
\(E=S=T=G\) before comparing signed Paulis. An inner join or
`sdim_equals_stim=true` is not full coverage.

SDIM owns no PEPS state, fidelity, BLP, performance, qutrit, prime-\(d\),
composite-\(d\), leakage, or live-carrier correctness claim.

## 9. Stress-test trip wires

| trip wire | result | bounded reason |
|---|---|---|
| symmetry/theorem | SURVIVES | exact \(p=0\) factorization and unitary invariance are registered; no monotonic-entanglement premise remains |
| formulation invariance | SURVIVES | persistent memory, entropy, bond, fixed-mask BLP, and mixture-map BLP remain distinct |
| rate-versus-observable | SURVIVES | the discrete object is labelled a sampled, fixed-pair BLP-derived witness |
| independent ground truth | SURVIVES | complete NumPy/stdlib dense evolution and a backend-free comparator differ materially from both candidates |
| degenerate design | SURVIVES | independent dense revival and four-lane positive truncation are preconditions for selection |
| suppressing lens | SURVIVES | fixed pair, finite masks, finite widths, and endpoint sampling are explicit; nulls remain inconclusive |
| un-led reproduction | SURVIVES | source equations, sign bridge, ensemble repair, and protocol repairs received independent rereviews |
| predict-before-measure | SURVIVES | hypotheses, bands, population, controls, selection, and failure branches precede implementation and target execution |
| propagation audit | SURVIVES | forbidden claims block Record, Markovian-null, Campbell-equivalence, generic PEPS, qutrit/leakage, and universal-efficiency propagation |

`SURVIVES` is bounded to this exact preregistration. It is not theorem-grade
validation of PEPS contraction or GCAPEPS as a production Carrier.

## 10. Retrieval and engineering integrity

The following local checks were rerun from the repository root in the `ecs`
environment:

| check | observed status |
|---|---|
| `python tools/literature_rag.py validate` | RAG artifact valid against the live corpus |
| `python tools/literature_kg.py validate` | knowledge graph valid against the live corpus |
| `python scripts/rebuild_current_corpus_manifest.py --check` | 288 candidates, 47 audit-valid, 47 admitted, 0 orphaned, 0 stale, `OK` |
| `python -m pytest -q tests/test_literature_tools.py` | 69 passed |
| `python tools/check_reading_order.py` | 28 references, 0 missing, newest record named, HEAD `736683c`, 0 commits since reconciliation, `OK` |

At the user's explicit request, a separate AnySearch academic-vertical
disconfirmation/discovery pass was also run on 2026-07-29 using public queries
for BLP distinguishability, finite-memory collision models, partial SWAP, and
Markovian embedding. It recovered the expected McCloskey--Paternostro and
Campbell records and adjacent BLP/collision-model reviews. It exposed no
contradiction that changes the frozen claim boundary. AnySearch output is
discovery metadata only: it was not admitted as equation-level evidence and
does not replace the fixed PDFs or their exact-locator audits.

All checks in this section establish retrieval, manifest, parser, test, or
discovery integrity only. They do not establish the physical mechanism, BLP
witness, complete-state faithfulness, performance, or any future result.

## 11. Final gate

| prerequisite | verdict |
|---|---|
| load-bearing premises closed at exact primary-source locators | PASS |
| source anomalies preserved rather than silently repaired | PASS |
| finite-mixture aggregation order exact and common-map safe | PASS |
| mechanism and observable separated | PASS |
| standard metrics and project thresholds classified | PASS |
| predictions frozen before results | PASS |
| independent complete-state truth feasible and specified | PASS |
| simplifications bounded or paired with complete dense comparison | PASS |
| non-degenerate controls and constraint falsifiers registered | PASS |
| evaluator/calibration firewall frozen | PASS |
| working-directory and namespace contracts consistent | PASS |
| exactly one post-replay serialization leaf | PASS |
| timing/resource scopes and censor population frozen | PASS |
| SDIM role and exclusion boundary frozen | PASS |
| allowed and forbidden claims exhaustive | PASS |

```text
premises closed?                     yes
standard metric bound?               yes
predictions frozen?                  yes
independent ground truth?            yes
constraint falsifiers registered?    yes
simplifications bounded?             yes
controls registered?                 yes
P0                                   0
P1                                   0
final verdict                        PASS_TO_THEORY_ONLY_COMMIT
```

The next allowed action is a theory-only commit containing the exact reviewed
packet and this rereview. Implementation remains blocked until that commit
exists and its commit/tree plus all required complete-file hashes are bound as
specified by the preregistration. This rereview authorizes no result, Carrier,
Record, qutrit, leakage, generic PEPS, or universal GCAPEPS claim.
