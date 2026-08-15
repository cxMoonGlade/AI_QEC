# Czarnik, Dziarmaga, and Corboz arXiv:1811.05497v2 — source-only audit

Date: 2026-07-27  
Status: `DRAFT_PENDING_FRESH_INDEPENDENT_REVIEW`  
Prepared by: `/root/review_masot_source`  
Source: arXiv:1811.05497v2  
Scope: source claims, equations, figures, operation replay, source-local gaps, and bounded project application

This audit accompanies the candidate reading note
`docs/papers/reading_notes/czarnik_dziarmaga_corboz_ipeps_time_evolution_1811.05497v2_source_review.md`.
It is not an independent admission review and does not authorize manifest
admission.

## 1. Pinned source and review protocol

| field | value |
|---|---|
| title | *Time Evolution of an Infinite Projected Entangled Pair State: an Efficient Algorithm* |
| authors | Piotr Czarnik, Jacek Dziarmaga, Philippe Corboz |
| version | arXiv:1811.05497v2 |
| title-page date | 15 January 2019 |
| arXiv footer | v2, 14 January 2019 |
| source URI | `https://arxiv.org/abs/1811.05497v2` |
| source artifact | `docs/papers/1811.05497v2.pdf` |
| SHA-256 | `a29c4bf23e381c50cae91a708456d6240792302bf1c0e127348cd2c6fdc5639c` |
| extent | 13 pages, 14 figures, 3 tables, two appendices |

The canonical 3,499,982-byte PDF is an unencrypted PDF 1.5 object. Its complete
13-page text was read from title page through bibliography. All 13 pages were
rendered and visually inspected; pages 1–12 contain the load-bearing equations,
figures, tables, convergence statements, or numerical resource details. Text
extraction was used only for traversal and full-text absence searches.

The source was read before this audit and the candidate note were written. No
legacy Czarnik note was found or used.

## 2. Source question and bounded answer

The source asks how real, Lindbladian, and imaginary-time evolution of an
infinite PEPS can be advanced without retaining the enlarged virtual bond
dimension created by every local time-evolution gate.

Its central construction is:

1. decompose evolution into local Suzuki–Trotter gates;
2. apply a gate to obtain an exact post-gate iPEPS whose acted bond grows from
   \(D\) to \(kD\), with \(k\le d^2\), and specifically to \(2D\) for the
   Ising \(ZZ\) gate used in the implementation;
3. replace the enlarged tensors at one auxiliary bond by tensors with the
   original \(D\);
4. optimize those tensors, and optionally an ancilla disentangler, against a
   local bond-fidelity objective evaluated with a CTMRG bond environment;
5. place the locally optimized tensors on every equivalent bond to obtain the
   global approximate post-step iPEPS with bond dimension \(D\).

The paper provides empirical Ising-model benchmarks for this approximation. It
does not prove a global accumulated-error theorem, an exact contraction result,
or a universal efficiency or real-time reach theorem.

## 3. Notation and variant ledger

| symbol | source meaning | fixed or variable | exact source location |
|---|---|---|---|
| \(d\) | local physical Hilbert-space dimension | model-fixed | Sec. II, p. 1 |
| \(D\) | retained iPEPS virtual bond dimension | convergence/resource control | Sec. II, p. 1 |
| \(D'\) | abstract enlarged post-step bond dimension, \(D'>D\) | transient | Abstract, p. 1 |
| \(kD\) | enlarged acted bond after a nearest-neighbour gate, \(k\le d^2\) | gate-dependent | Sec. II, p. 1 |
| \(2D\) | enlarged bond for the paper's rank-two \(ZZ\)-gate decomposition | transient | Sec. III.D, Eq. (11) and Fig. 2, p. 4 |
| \(\chi\) | CTMRG environmental bond dimension | contraction-refinement parameter | Sec. III.E, pp. 4–5 |
| \(|\psi\rangle\) | input iPEPS before the considered gate layer | step-dependent | Secs. II–III, pp. 1–4 |
| \(|\psi'\rangle\) | exact state after the gate and optional ancilla disentangler, with enlarged acted bonds | transient target | Sec. III.D, p. 4 |
| \(|\widetilde\psi''\rangle\) | auxiliary network equal to \(|\psi'\rangle\) except at one truncated bond | local variational state | Sec. III.E, p. 4 |
| \(|\psi''\rangle\) | global approximate post-gate iPEPS obtained by tiling the locally optimized tensors | next retained state | Sec. III.E, p. 4 |
| \(A,B\) | two checkerboard input tensors | step-dependent | Sec. III.C and Fig. 2, pp. 3–4 |
| \(A',B'\) | exact post-gate tensors with enlarged connecting bond | transient | Sec. III.D and Fig. 2(c), p. 4 |
| \(A'',B''\) | optimized tensors with original connecting bond dimension \(D\) | variational output | Sec. III.E and Fig. 2(d), p. 4 |
| \(F\) | source's printed global-fidelity objective for \(|\psi''\rangle\) against \(|\psi'\rangle\) | optimization objective | Eq. (12), p. 4 |
| \(\widetilde F\) | source's printed one-bond local-fidelity objective for \(|\widetilde\psi''\rangle\) against \(|\psi'\rangle\) | optimized surrogate | Eq. (13), p. 4 |
| \(g\) | two-ancilla unitary gauge/disentangler on an acted bond | optional variational tensor | Eqs. (4), (11) context, and Fig. 2, pp. 3–4 |
| \(\beta\) | inverse temperature | evolution coordinate | Sec. III.A, Eqs. (2)–(5), p. 3 |
| \(\widetilde\beta\) | thermal critical exponent, renamed to avoid collision with inverse temperature | fitted exponent | Sec. IV.D, Eqs. (21)–(23), p. 8 |

Algorithm labels are source-specific:

- `eeFUd`: enlarged-state \(|\psi'\rangle\) environment with ancilla
  disentanglers;
- `eeFU`: enlarged-state environment without disentanglers;
- `FUd`: cheaper previous-state \(|\psi\rangle\) environment with
  disentanglers;
- `FU`: previous-state environment without disentanglers; for pure-state real
  time, unitary cancellations reduce the source's eeFU construction to FU;
- `SU`: pairwise SVD truncation that ignores long-range bond-environment
  correlations.

The adjective “exact” in `exact-environment` distinguishes a
\(|\psi'\rangle\)-based environment from reuse of the previous
\(|\psi\rangle\) environment. It does not mean that the infinite tensor network
is contracted exactly: the bond environment is obtained approximately by
finite-\(\chi\) CTMRG.

## 4. Formula and operation reconstruction

### 4.1 Evolution and bond enlargement

The second-order step is printed as

\[
U(d\tau)=U_h(d\tau/2)U_{ZZ}(d\tau)U_h(d\tau/2),
\]

with \(U_{ZZ}\) split into four commuting horizontal/vertical gate layers.
For the considered bond, the Ising gate has the rank-two factorization

\[
e^{i d\tau Z_jZ_{j'}}
 = \sum_{\mu=0,1} z_{j,\mu}z_{j',\mu},
\]

where \(z_{j,\mu}=\sqrt{\Lambda_\mu}(Z_j)^\mu\),
\(\Lambda_0=\cos d\tau\), and \(\Lambda_1=i\sin d\tau\). Contracting the local
gate factors into \(A,B\) produces \(A',B'\) connected by a bond of dimension
\(2D\). The general outline states \(kD\), \(k\le d^2\).

For thermal purification, the same bond update can include a unitary \(g\) on
the corresponding ancillas. This gauge cancels from the reduced Gibbs operator
after tracing the ancillas; the source optimizes it to reduce the required
retained \(D\).

### 4.2 Global objective versus local surrogate

Equation (12) prints

\[
F=
\frac{
\langle\psi''|\psi'\rangle
\langle\psi'|\psi''\rangle
}{
\langle\psi''|\psi''\rangle
}.
\]

Equation (13) replaces the global approximate state with the one-bond
auxiliary state:

\[
\widetilde F=
\frac{
\langle\widetilde\psi''|\psi'\rangle
\langle\psi'|\widetilde\psi''\rangle
}{
\langle\widetilde\psi''|\widetilde\psi''\rangle
}.
\]

The paper calls these quantities fidelities. Neither printed expression divides
by \(\langle\psi'|\psi'\rangle\). Since the target is fixed during each local
optimization, an omitted target-only factor would not change the optimizer, but
the source does not state a normalization convention that licenses treating the
printed value as a normalized absolute fidelity.

The locally optimized \(A'',B''\) are then placed at all equivalent sites. The
source explicitly says this global placement is an approximation relative to
direct global optimization. Its argument that the approximation should be
accurate assumes \(D\) is large enough that truncation errors are negligible;
no theorem or accumulated-error inequality is derived.

### 4.3 CTMRG environment and optimizer

The rank-six bond environment is obtained approximately by CTMRG with
environmental bond dimension \(\chi\). The paper calls CTMRG the numerical
bottleneck and says all results were checked for convergence with increasing
\(\chi\).

The same environment enters all overlaps in \(\widetilde F\) and is independent
of \(A'',B''\), and \(g\), so it is computed once for the local optimization.
For fixed \(A'',B''\), the disentangler is updated by an SVD of its environment.
For a fixed partner tensor and \(g\), each local tensor is updated with a metric
pseudoinverse. The source iterates

\[
\cdots\rightarrow g\rightarrow A''\rightarrow B''\rightarrow\cdots
\]

until self-consistency and convergence of \(\widetilde F\).

Appendix B uses relative change below \(10^{-10}\) in the two-site reduced
tensor environment's 2-norm per CTMRG iteration as its convergence criterion.
This is an iterative numerical stopping rule, not a state-fidelity or
observable-error certificate.

### 4.4 Environment reuse

The cheaper FU variant evaluates the local update with the previous
\(|\psi\rangle\) environment rather than the enlarged
\(|\psi'\rangle\) environment. The paper first gives a simple error-propagation
argument under which the environment difference is linear in \(d\beta\) and
would not disappear from the final state merely by decreasing \(d\beta\). It
then reports that the two variants give similar magnetization and fitted
critical data for the studied bias-smoothed thermal Ising workloads.

The empirical comparison limits the concern for those workloads; it does not
prove general equivalence of the two environment choices.

## 5. Empirical accuracy and resources

### 5.1 Real and Lindbladian time

Figure 5 reports that larger \(D=2,\ldots,8\) improves energy conservation and
extends the time range over which transverse magnetization appears converged
after the three tested Ising quenches. Figure 6 reports the same qualitative
increase of the apparent convergence window for a specified dissipative Ising
evolution.

The source also gives the physical limitation: after a generic sudden quench,
oppositely moving entangled quasiparticles make entanglement entropy grow
asymptotically linearly, so a fixed-resource tensor network is expected to fail
after a finite evolution time. This is a qualitative source statement and
motivation, not a universal quantitative time-horizon theorem.

### 5.2 Thermal accuracy

The reported \(D=5\) thermal critical-temperature fits are:

| \(h_x\) | source estimate | cited QMC estimate | source-reported relative accuracy |
|---:|---:|---:|---:|
| 2.5 | \(T_c=1.2745(7)\) | \(1.2737(6)\) | about \(0.1\%\) |
| 2.9 | \(T_c=0.6055(10)\) | \(0.6085(8)\) | about \(0.5\%\) |

The \(h_x=2.5\) calculation reports convergence at \(d\beta=0.002\) and
\(\chi=25\); the \(h_x=2.9\) calculation reports \(d\beta=0.005\) and
\(\chi=25\). The QMC numbers are cited external reference data, not an
independent computation reproduced in this source.

At \(h_x=2.9\), Table I reports that disentanglers greatly improve the \(D=4\)
critical estimates, while the \(D=5\) eeFU and eeFUd estimates are similar.
The improvement costs more local-optimization iterations and larger reduced
tensors, but the paper says that loop remains sub-leading to CTMRG.

Table II reports statistically compatible FU and eeFU fitted critical data for
the two tested transverse fields. Table III gives a contrary efficiency result
for further simplification: in the reported \(h_x=2.9\) example, \(D=12\) SU
takes longer and gives substantially poorer fitted critical data than \(D=5\)
FU.

### 5.3 Resource facts and limits

Appendix A reports:

- a full spin-\(1/2\) tensor has \(4D^4\) elements in the stated counting;
- the larger reduced tensor used with disentanglers has \(16D^2\) elements;
- without disentanglers, the smaller reduced tensor has \(4D^2\) elements.

Appendix B reports 5–6 days on a 14-core, 2.20 GHz Intel Xeon Gold 5120
processor to obtain the \(h_x=2.9\), \(D=5\) full-update
\(T_c\) and \(1/\widetilde\beta\delta\) estimates in Table II.

The source does not report peak memory, energy use, code version or commit, or
a matched Clifford-augmented/full-PEPS benchmark.

## 6. Assigned closure rows

| assigned row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| each Trotter update enlarges and then restores the bond | Abstract and Sec. II, p. 1; Eq. (11)/Fig. 2, p. 4 | \(D\to D'>D\), generally \(D\to kD\), and \(2D\) for the displayed \(ZZ\) gate, followed by approximation back to \(D\) | no global accumulated truncation-error bound | `CLOSED_AT_ALGORITHM_LEVEL` |
| global fidelity versus local bond fidelity | Eqs. (12)–(13), p. 4 | direct global optimization is replaced by a one-bond surrogate, then tiled globally | no theorem that maximizing \(\widetilde F\) maximizes \(F\), and no stated target-normalization convention | `CLOSED_AS_PRINTED_OBJECTIVES; GUARANTEE_MISSING` |
| CTMRG/environment approximation | paragraph after Eq. (13), p. 4; Fig. 3 and Sec. III.E, p. 5; App. B, p. 12 | finite-\(\chi\) approximate environment, convergence checks, bottleneck, and stopping rule | no certified state or observable error from \(\chi\) | `CLOSED_AS_APPROXIMATE_NUMERICS` |
| empirical accuracy and resources | Figs. 5–13 and Tables I–III, pp. 6–11; App. A–B, p. 12 | workload-specific convergence, QMC comparisons, tensor-size counts, and one CPU wall-time | no general complexity theorem, peak memory, or universal accuracy law | `CLOSED_FOR_REPORTED_WORKLOADS` |
| real-time entanglement barrier | Sec. II real-time paragraph, p. 2; Fig. 5, p. 6 | linear entanglement growth motivates a finite useful time, while larger \(D\) extends observed convergence | no universal formula for the reachable time versus \(D\) | `CLOSED_AS_QUALITATIVE_LIMITATION` |
| selective measurement instrument | Sec. IV.B, Eq. (19), p. 7 | ensemble density-matrix Lindblad evolution after vectorization | no outcome-resolved Kraus instrument or sampled trajectory | `MISSING` |
| reset transaction | Sec. IV.B, Eq. (19), p. 7 | Hamiltonian plus local lowering dissipator | no reset channel, post-reset state, or reset invariant | `MISSING` |
| Born branch history | Sec. IV.B, Eq. (19), p. 7 | deterministic master-equation evolution | no Born branch masses, normalized conditional branches, prefix masses, or branch completeness | `MISSING` |
| complete Record law | Sec. IV.B and Fig. 6, p. 7 | expectation-value time series | no ordered raw outcomes, detector fold, logical-observable fold, or Record distribution | `MISSING` |
| Clifford augmentation | Sec. III.A and Fig. 1, p. 3 | the state/purification is represented directly as an iPEPS | no Clifford frame, stabilizer tableau, Pauli pull-through, or augmented residual representation | `MISSING` |
| matched CAPEPS/full-PEPS efficiency | App. A–B, p. 12 | internal iPEPS tensor-size and runtime facts | no CAPEPS arm or matched accuracy/runtime/peak-memory comparison against full PEPS | `MISSING` |

## 7. Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| iPEPS \(|\psi\rangle\) with retained \(D\) | second-order Suzuki–Trotter factorization | sufficiently small \(d\tau\) for the chosen discretization | ordered one-site and two-site gate layers | Eqs. (6)–(10), p. 3 | `CLOSED` |
| one two-site \(ZZ\) gate | rank-two SVD/operator factorization | Ising interaction used in the implementation | site factors with \(\mu=0,1\) | Eq. (11), p. 4 | `CLOSED` |
| \(A,B\) and local gate factors | contract the factors into the site tensors; optionally apply ancilla \(g\) | same checkerboard gate on each considered bond | exact \(A',B'\) joined by \(2D\), giving \(|\psi'\rangle\) | Sec. III.D and Fig. 2(b,c), p. 4 | `CLOSED` |
| infinite \(|\psi'\rangle\) double layer | approximate its bond environment by CTMRG | chosen \(\chi\) and iterative stopping rule | reusable rank-six bond environment | Sec. III.E, pp. 4–5; App. B, p. 12 | `CLOSED_AS_APPROXIMATE` |
| \(|\psi'\rangle\) plus one \(D\)-bond replacement | form \(|\widetilde\psi''\rangle\) and optimize \(\widetilde F\) | local metric pseudoinverse and iterative convergence | optimized \(A'',B''\), optionally \(g\) | Eqs. (13)–(18), pp. 4–6 | `CLOSED` |
| optimized local tensors | place them at all equivalent bonds | translational checkerboard ansatz; local-to-global approximation | global \(|\psi''\rangle\) with retained \(D\) | paragraph after Eq. (13), p. 4 | `CLOSED_AS_SOURCE_APPROXIMATION` |
| retained \(|\psi''\rangle\) | continue remaining gate layers and time steps | repeated truncation accepted | evolved fixed-\(D\) iPEPS | Sec. II and Sec. III, pp. 1–6 | `CLOSED_AT_ALGORITHM_LEVEL` |
| evolved iPEPS | CTMRG contraction and observable evaluation | empirical convergence in \(D,\chi,d\tau\) or \(d\beta\) | magnetization, energy error, or thermal critical fits | Sec. IV and App. B, pp. 6–12 | `CLOSED_FOR_REPORTED_OBSERVABLES` |
| vectorized density matrix | apply the real-time machinery to the Lindblad generator | ensemble master equation, not trajectory sampling | iPEPS isomorphic to an iPEPO density operator | Eq. (19) and text, p. 7 | `CLOSED_AT_ENSEMBLE_LEVEL` |

The operation chain is replayable at the level published by the source. The
local-to-global error guarantee, CTMRG certification, and stochastic
instrument/Record transformations are absent rather than silently inferred.

## 8. Source-local anomalies and limitations

1. The source's “exact-environment” name refers to the enlarged
   \(|\psi'\rangle\) environment, but the environment tensor is obtained by an
   explicitly approximate CTMRG contraction.
2. Eqs. (12)–(13) omit a target-state norm while calling the printed objectives
   fidelities. The fixed target makes its norm irrelevant to the optimizer, but
   the source does not state an absolute normalization convention.
3. The accuracy argument for tiling a locally optimized bond assumes \(D\) is
   large enough for negligible truncation error; no global theorem follows.
4. The old-environment FU equivalence is numerical evidence for two
   bias-smoothed thermal Ising workloads, not a formulation-invariance result.
5. CTMRG convergence and the \(10^{-10}\) environment-change threshold are
   numerical diagnostics, not an independent state/observable error bound.
6. The real-time barrier is qualitative; the paper reports apparent
   \(D\)-convergence windows but no universal reachable-time scaling.
7. The strongest efficiency comparison is source-local: \(D=12\) SU is slower
   and less accurate than \(D=5\) FU in one thermal Ising example.
8. The only explicit wall-time is 5–6 days for one fitted-data workload on one
   CPU configuration; peak memory and implementation provenance are absent.

## 9. Project application

The direct reusable source object is a full-iPEPS compression pattern:

\[
D \longrightarrow kD \longrightarrow D
\]

with a locally optimized bond surrogate, an approximate CTMRG environment, and
empirical convergence checks. This can inform how a full-PEPS baseline or
compression lens is described.

The following bridges are project inference, not paper claims:

- applying the local-fidelity surrogate to a QEC circuit or to a
  Clifford-augmented PEPS residual;
- treating \(\widetilde F\), CTMRG convergence, magnetization convergence, or
  energy conservation as a certificate for a complete measurement Record;
- mapping deterministic Lindblad evolution to sampled syndrome histories;
- inferring a CAPEPS resource advantage from the paper's FU/SU or reduced-tensor
  comparisons;
- converting the qualitative real-time entanglement barrier into a fixed QEC
  circuit-depth limit.

No sentence in this audit should be cited as though the source established
those bridges.

## 10. Competing evidence and kill conditions

No external contrary source was assigned. The paper contains its own
disconfirmation surface:

- direct global fidelity optimization is described as more accurate in
  principle than the local surrogate;
- replacing the enlarged-state environment by the old-state environment has a
  source-articulated first-order error concern before the limited empirical
  comparison;
- simple update permits larger \(D\) but performs worse and can take longer in
  the reported critical-data example;
- generic real-time entanglement growth imposes a finite useful horizon.

Any project use is killed or reopened if:

1. the claim requires a proved global/state/Record error bound rather than a
   local surrogate and empirical convergence;
2. finite-\(\chi\) CTMRG or \(D\)-truncation changes the target observable under
   an independent reference;
3. selective outcome probabilities, conditional states, reset, or detector
   Records are load-bearing;
4. a claimed resource advantage lacks matched accuracy, hardware, runtime, and
   peak-memory arms in the target workload;
5. the target evolution lies beyond the empirically converged \(D\)-window or
   exhibits unbounded real-time entanglement growth.

## 11. Source-only verdict

| row | verdict |
|---|---|
| Trotter-gate bond enlargement \(D\to kD\) and compression to \(D\) | `CLOSED` |
| global objective \(F\) and local bond objective \(\widetilde F\) | `CLOSED_AS_PRINTED` |
| theorem connecting local and global fidelity | `MISSING` |
| CTMRG environment construction | `CLOSED_AS_APPROXIMATE_NUMERICS` |
| certified CTMRG/truncation error bound | `MISSING` |
| thermal and dynamical empirical benchmarks | `CLOSED_FOR_REPORTED_ISING_WORKLOADS` |
| reduced-tensor counts and one CPU wall-time | `CLOSED` |
| universal runtime, memory, accuracy, or scaling advantage | `MISSING` |
| finite-time real-time entanglement barrier | `CLOSED_AS_QUALITATIVE_SOURCE_LIMITATION` |
| selective measurement instrument and Born branches | `MISSING` |
| reset transaction | `MISSING` |
| branch-history or complete Record law | `MISSING` |
| Clifford/stabilizer augmentation | `MISSING` |
| matched CAPEPS/full-PEPS efficiency result | `MISSING` |
| executable code/revision provenance | `MISSING` |

Read status: `complete`  
Evidence status: `persisted`  
Operation replay status: `complete_with_explicit_source_gaps`  
Candidate admission status: `draft_pending_fresh_independent_review`
