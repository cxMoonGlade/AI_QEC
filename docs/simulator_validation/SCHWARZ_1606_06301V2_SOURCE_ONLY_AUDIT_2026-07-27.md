# Schwarz et al. arXiv:1606.06301v2 — source-only audit

Date: 2026-07-27
Status: `SOURCE_ONLY_REVIEWED`
Independent admission reviewer: `independent_schwarz_1606_source_rereview_2026_07_27`
Independent admission basis: `docs/simulator_validation/SCHWARZ_1606_06301V2_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`
Independent admission basis SHA-256: `8a9b69e1e9cd93db9469a295801b1336ba7f4dd841a28db30ee89d32f90d1bd2`
Independent reconstruction basis: `docs/simulator_validation/SCHWARZ_1606_06301V2_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`
Source: arXiv:1606.06301v2
Scope: source claims, theorem hypotheses, equations, operation replay, printed anomalies, and source-local absences

This packet was reconstructed from the pinned full text rather than from an
abstract, retrieval cache, or prior project narrative. All seven PDF pages were
read in order and visually inspected. The pre-existing independent
reconstruction was used as a disconfirmation checklist, not as a substitute
for source reading. A separate fresh source-first reviewer then checked every
claim, locator, theorem boundary, anomaly, gap, and schema record and returned
a bounded source-only PASS.

## 1. Pinned source

| field | value |
|---|---|
| title | *Approximating local observables on projected entangled pair states* |
| authors | M. Schwarz, O. Buerschaper, J. Eisert |
| version | arXiv:1606.06301v2, version stamp 29 August 2016 |
| source URI | `https://arxiv.org/abs/1606.06301v2` |
| source artifact | `docs/papers/1606.06301v2.pdf` |
| SHA-256 | `bc240a9b78a84e886360d4d0a621a0b06b12fef93e4e399c6b9aa1f66d1e43c3` |
| extent | 7 pages: four-page main text, references, and a three-page appendix |
| visual verification | PDF pages 1–7 |

## 2. Source question and bounded answer

The paper asks whether local expectation values can be approximated more
efficiently for a restricted class of physically motivated PEPS than for
arbitrary PEPS.

Its proved result is conditional. Theorem 1 takes an unnormalised injective
PEPS on a constant-dimensional regular lattice, with finite physical
dimension, bond dimension \(D\), a uniformly gapped family of prefix parent
Hamiltonians, and controlled tensor condition numbers. For an observable
\(O_X\) supported on fewer than a constant number of sites, it approximates the
single normalized expectation

\[
\frac{\langle\omega|O_X|\omega\rangle}
     {\langle\omega|\omega\rangle}
\]

to additive absolute error \(\epsilon\) by removing a boundary around \(X\)
and exactly contracting the resulting finite patch.

This is not a theorem that arbitrary PEPS are efficiently contractible. It is
also not a global state-fidelity bound, a numerical finite-bond truncation
certificate, or an outcome-resolved measurement/reset/Record theorem.

## 3. Conjectures and theorem are different objects

### 3.1 Weak PEPS conjecture

Conjecture 1 starts with a local Hamiltonian \(H=\sum_i h_i\) on a regular
lattice, a constant gap above a unique ground state \(\rho\), and a
constant-support observable \(O_X\). It conjectures existence of a PEPS
\(\omega\) with bond dimension polynomial in \(N\) and \(\epsilon^{-1}\)
whose expectation of that one local observable differs from the ground-state
expectation by less than \(\epsilon\) (PDF p. 2).

The neighboring trace-norm and relative-entropy statements are introduced for
the one-dimensional MPS discussion. The higher-dimensional conjecture itself
does not assert global trace distance or global fidelity.

### 3.2 Strong PEPS conjecture

Conjecture 2 additionally asks for the approximating PEPS to be injective and
for its parent Hamiltonian to have a constant gap (PDF p. 2). The paper states
that neither conjecture captures non-injective PEPS, non-unique ground states,
or intrinsic topological order.

Conjecture 2 is not Theorem 1. The theorem begins with a PEPS already obeying
its assumptions. The conjecture is a proposed existence bridge for suitable
gapped ground states and cannot be promoted to a proved generic-PEPS premise.

## 4. Notation and assumption ledger

| object | source definition or role | exact locator | consequence for use |
|---|---|---|---|
| \(H=\sum_i h_i\), \(\rho\), \(\Delta\) | local Hamiltonian, unique ground state, and constant spectral gap used in Conjectures 1–2 | p. 2, opening PEPS-conjecture paragraph | these are not the prefix Hamiltonians used in Theorem 1's proof |
| \(A_v\) | local map from virtual indices to one physical index | p. 3, Eq. (2) and preceding definition | the proof removes boundary maps using their left inverses |
| injectivity | each blocked local map has a Moore–Penrose left inverse; blocking may join a constant number of adjacent tensors | p. 3, paragraph after Eq. (2) | the proof does not cover generic non-injective or topological PEPS |
| \(H_t\) | parent Hamiltonian of the prefix/sub-PEPS \(\{A_v\}_{0\leq v\leq t}\) | p. 3, uniform-gap definition | the required gap is not merely a terminal gap for \(H_N\) |
| \(\Delta_*\) | common lower bound \(\Delta_t\geq\Delta_*\) for every prefix parent Hamiltonian | p. 3, uniform-gap definition | exponential clustering is invoked at every boundary-removal step |
| \(\kappa_*\) | \(\max_i\kappa(A_i)\) | p. 2, Theorem 1; p. 6, Eqs. (13)–(15) | the per-step error contains \(\kappa(A_i)^2\), and useful scaling needs controlled condition numbers |
| \(O_X\) | observable supported on \(|X|<k\) sites for constant \(k\); \(X\) may be disconnected | pp. 2–3, Theorem 1 and following paragraph | fixed-order correlations are included; extensive/global observables are not |
| \(d\) | printed for both lattice dimension and physical spin dimension | pp. 2–3, Theorem 1 and preliminaries | formulas such as \((Dd)^{O(\ell^d)}\) overload two distinct dimensions |
| \(\ell\) | graph-distance patch radius around \(X\) | p. 2, Eq. (1); p. 6, Eq. (15) | patch volume is of order \(\ell^{d_{\mathrm{lat}}}\) after disambiguating the overloaded \(d\) |

## 5. Theorem statement and complexity boundary

Theorem 1 (PDF p. 2) gives

\[
\left|
\frac{\langle\omega|O_X|\omega\rangle}
     {\langle\omega|\omega\rangle}
-\widetilde O_X
\right|\leq\epsilon
\]

for

\[
\ell\in O\!\left(
\frac{2\ln\kappa_*+\ln(\epsilon^{-1})+\ln\|O_X\|}
     {\Delta_*}
\right).
\tag{1}
\]

The printed deterministic classical cost is
\((Dd)^{O(\ell^d)}\). Because the source overloads \(d\), a faithful
typed reading is
\((D d_{\mathrm{phys}})^{O(\ell^{d_{\mathrm{lat}}})}\), not a change to
the theorem but a disambiguation of its two uses. With constant lattice and
physical dimensions, constant \(\Delta_*\), polynomially bounded \(D\),
\(\kappa_*\), \(\epsilon^{-1}\), and \(\|O_X\|\), Eq. (1) gives
\(\ell=O(\log N)\), so the displayed classical cost is quasi-polynomial in
general fixed spatial dimension. The paper separately says the one-dimensional
MPS case is polynomial.

The printed quantum cost is
\(\widetilde O(\ell^d/\epsilon^2)\) with depth
\(O(\operatorname{polylog}(\ell/\epsilon))\). This quantum arm relies on
the external PEPS preparation method cited as Ref. 32 and repeated independent
measurement of one observable; the present paper does not rederive that
preparation algorithm.

## 6. Operation replay

| input | transformation | required assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| virtual maximally entangled pairs and local maps \(A_v\) | apply every \(A_v\) | finite virtual/physical dimensions | PEPS \(|\psi\rangle=\bigotimes_vA_v\bigotimes_e|\phi_e\rangle\) | p. 3, Eq. (2) | `CLOSED` |
| injective PEPS | block a constant number of adjacent tensors | left inverse exists after constant blocking | individually left-invertible maps \(A_v\) | p. 3, injectivity paragraph | `CLOSED_UNDER_ASSUMPTION` |
| observable support \(X\) and radius \(\ell\) | order the final \(N_b=O(\ell^{d-1})\) tensors as a boundary around \(X\) | regular-lattice geometry and injectivity | normalized prefix states \(|\omega_i\rangle\) and parent Hamiltonians \(H_i\) | p. 3, proof sketch; p. 5, Eq. (8) | `CLOSED_UNDER_ASSUMPTION` |
| every prefix state \(|\omega_i\rangle\) | apply exponential clustering to \(O_X\) and a boundary operator \(O_i\) | every \(H_i\) has gap at least \(\Delta_*\) | connected-correlation bound | p. 3, Eq. (3); p. 5, Eq. (9) | `CLOSED_UNDER_UNIFORM_PREFIX_GAP` |
| one boundary tensor \(A_i\) | choose \(O_i=(A_i^{-1})^\dagger A_i^{-1}\), divide by its expectation, and identify the normalized previous prefix | finite inverse and condition number | one-step expectation change bounded by \(e^{-O(\ell\Delta_*)}\|O_X\|\kappa(A_i)^2\) | pp. 3–4, Eqs. (4)–(5); p. 6, Eqs. (10)–(13) | `CLOSED_ASYMPTOTIC` |
| all \(N_b\) boundary tensors | sum one-step errors by the triangle inequality | boundary size \(O(\ell^{d-1})\) | total additive scalar error \(\ell^{d-1}e^{-O(\ell\Delta_*)}\kappa_*^2\|O_X\|\) | p. 6, Eq. (14) | `CLOSED_ASYMPTOTIC` |
| target \(\epsilon\) | choose \(\ell\) according to Eq. (15) | constant gap and controlled \(\kappa_*\), \(\|O_X\|\) | a sufficient local patch radius | p. 6, Eq. (15) | `CLOSED_ASYMPTOTIC_NOT_NUMERICAL_CERTIFICATE` |
| state after boundary removal | use the exact patch/remainder tensor-product factorization | all boundary tensors removed as constructed | \(|\omega_*\rangle=|\omega_R\rangle\otimes|\omega_P\rangle\) | p. 6, Eqs. (16)–(17) | `CLOSED` |
| local observable on the factorized state | reduce the normalized remainder to scalar one | \(O_X\) acts only on the patch | normalized patch expectation | p. 6, Eq. (18) | `CLOSED` |
| finite patch tensor network | sum all patch indices exactly | finite dimensions and chosen patch | classical estimate with printed \((Dd)^{O(\ell^d)}\) cost | p. 6, paragraph after Eq. (18) | `CLOSED_WITH_OVERLOADED_d` |
| patch PEPS | prepare the patch using Ref. 32 | all Theorem 1 assumptions plus external preparation result | patch state within trace-distance error \(\epsilon\) | p. 7, quantum-computer discussion | `QUALIFIED_EXTERNAL_DEPENDENCY` |
| independently prepared patch copies | measure \(O_X\) and apply a Chernoff estimate | implicitly bounded/normalized sampling scale | expectation estimate from \(O(1/\epsilon^2)\) trials | p. 7, quantum-computer discussion | `QUALIFIED_MISSING_NORM_FACTOR` |

The mechanism-to-observable replay closes only for one normalized local
expectation and only under the stated hypotheses. No step yields a global
state approximation, an outcome-conditioned instrument, or a multi-time
measurement law.

## 7. Transfer-operator and LTQO statements

The main text explicitly says that the proof does not imply LTQO as defined in
Ref. 33. The proof adds boundary terms to retain a unique ground state, whereas
the cited LTQO definition only removes boundary Hamiltonian terms. The paper
claims a variant with unique ground states, not standard LTQO (PDF p. 4).

The transfer-operator appendix is also conditional. It assumes Conjecture 2,
all assumptions of Theorem 1, and translational invariance, then contracts all
sites outside a one-dimensional line \(L\). Equations (19)–(21) define the
site and line transfer operators and the correlation function. Under the
printed exponential-correlation statement in Eq. (22), Eqs. (23)–(24) infer

\[
\frac{\lambda_2}{\lambda_1}\leq e^{-c_2\delta}.
\]

This is not an unconditional gap theorem for every PEPS transfer operator or
every two-dimensional environment map. The printed derivation also contains
the unresolved \(\delta\), injectivity-direction, and diagonalizability issues
listed below.

## 8. Printed anomalies preserved

1. **Overloaded \(d\) (pp. 2–3, Theorem 1 and preliminaries).** The source
   uses \(d\) both for lattice dimension and physical dimension, including
   in \((Dd)^{O(\ell^d)}\).
2. **Hidden clustering constants (pp. 3–4 and 5–6, Eqs. (3)–(5) and
   (9)–(14)).** The bounds use \(e^{-O(\ell\Delta_*)}\) as an upper bound
   without exposing a positive decay constant or prefactor, so they are
   asymptotic statements rather than directly executable numerical
   certificates.
3. **Uncontrolled non-injective approximation sentence (p. 3, injectivity
   paragraph).** The paper says every non-injective PEPS is
   \(\epsilon\)-close to an injective one but gives no norm, construction,
   prefix-gap control, or condition-number control; that sentence does not
   extend Theorem 1 to non-injective PEPS.
4. **Constant-time wording omits \(D\) (p. 3, paragraph continuing Theorem
   1).** The prose lists constant \(d,\Delta_*,\kappa_*,\epsilon\), while
   the displayed runtime still depends on bond dimension \(D\). Constant
   deterministic time also requires bounded \(D\), or must be read only as
   constant in \(N\) under such a bound.
5. **Main/appendix equation cross-references (p. 4).** The main text refers
   to Eqs. (17) and (18) beside displays numbered (6) and (7); the appendix
   later repeats the objects as Eqs. (17) and (18).
6. **Quantum patch-size inconsistency (p. 7).** The proof obtains
   \(\ell=O(\log N)\), so a fixed-dimensional patch has
   \(O(\log^{d_{\mathrm{lat}}}N)\) spins, but p. 7 prints
   \(\ell^d=O(\log N)\) without an additional restriction or changed
   choice of \(\ell\).
7. **Sampling norm dependence omitted (p. 7).** The
   \(O(1/\epsilon^2)\) Chernoff count is stated without a
   \(\|O_X\|^2\), range, or variance factor, although Theorem 1 permits a
   general observable and Eq. (1) retains \(\|O_X\|\).
8. **Transfer injectivity direction (p. 7, transfer discussion).** The
   opening sentence says PEPS-to-line contraction makes MPS injectivity
   inherited by the PEPS; the later argument uses line-MPS injectivity as
   inherited from PEPS injectivity.
9. **Undefined \(\delta\) (p. 7, Eqs. (22) and (24)).** The symbol is not
   defined in the transfer section, leaving the quantitative relationship to
   the parent-Hamiltonian gap incomplete.
10. **Transfer spectral expansion assumption (p. 7, Eq. (23)).** The source
    writes a simple left/right eigenvector expansion but does not discuss
    non-diagonalizable transfer operators or Jordan blocks.

None of these anomalies is silently repaired in the source-only note. They
qualify the affected claim or appear as an atomic source-local gap.

## 9. Assigned closure rows

| assigned row | exact source location | paper says | paper does not say | source-local status |
|---|---|---|---|---|
| conditional local-observable approximation | Theorem 1 and Eq. (1), p. 2; Eqs. (8)–(18), pp. 5–6 | one normalized local expectation can be approximated to additive error under the theorem assumptions | arbitrary PEPS contraction is efficient | `CLOSED_CONDITIONAL` |
| injectivity after blocking | p. 3, injectivity paragraph | a constant blocked map has a Moore–Penrose left inverse | generic non-injective or G-injective PEPS satisfy the theorem | `CLOSED_AS_ASSUMPTION` |
| uniformly gapped prefix parent Hamiltonians | p. 3, definition; p. 5 after Eq. (8) | every prefix \(H_t\) has gap at least \(\Delta_*\) | a gap only for terminal \(H_N\) suffices | `CLOSED_AS_ASSUMPTION` |
| controlled condition number | Theorem 1, p. 2; Eqs. (13)–(15), p. 6 | error contains \(\kappa_*^2\), and radius contains \(2\ln\kappa_*\) | conditioning is automatic or representation-independent | `CLOSED_AS_ASSUMPTION` |
| constant dimensions and local support | Theorem 1, pp. 2–3 | lattice dimension is constant, spin dimension finite/treated as constant in scaling, and \(|X|<k\) for constant \(k\) | extensive/global observables or arbitrary graphs are covered | `CLOSED_AS_ASSUMPTION` |
| error object | Theorem 1, p. 2 | additive absolute error in one normalized scalar expectation | state trace distance, global fidelity, or Record TV | `CLOSED` |
| deterministic cost | Theorem 1, pp. 2–3; after Eq. (18), p. 6 | \((Dd)^{O(\ell^d)}\), quasi-polynomial in the stated controlled regime | generic polynomial-time two-dimensional PEPS contraction | `CLOSED_WITH_NOTATION_QUALIFICATION` |
| quantum cost | Theorem 1, p. 2; quantum discussion, p. 7 | external patch preparation plus repeated measurements gives the printed quantum time and depth | a self-contained preparation proof or arbitrary-norm sample bound | `QUALIFIED` |
| standard LTQO | p. 4, LTQO discussion | only a boundary-term variant with unique ground states follows | standard LTQO as defined in Ref. 33 follows | `CONTRADICTED_BY_SOURCE` |
| conditional line-transfer gap | pp. 4 and 7, Eqs. (19)–(24) | a conditional induced one-dimensional transfer-gap argument is presented | all PEPS transfer/environment operators are gapped | `QUALIFIED_BY_PRINTED_ANOMALIES` |
| generic/non-injective PEPS | pp. 2–4, conjecture, injectivity, and conclusion passages | non-injective PEPS are outside the conjectures/theorem; G-injective extension is future work | the theorem covers generic non-injective PEPS | `MISSING` |
| intrinsic topological PEPS | p. 2, paragraph after Conjecture 2 | intrinsic topological order is not captured | degenerate sectors or topological PEPS are covered | `MISSING` |
| global state fidelity | p. 2, Conjecture 1; p. 2, Theorem 1 | only local expectations are controlled in higher dimensions | a global trace-distance or fidelity guarantee | `MISSING` |
| measurement branches | p. 7 quantum discussion; full-text boundary | independent preparations are measured to estimate \(O_X\) | outcome-resolved Born masses or conditional states | `MISSING` |
| reset instrument | full-text boundary | no reset operation is defined | reset transaction or post-reset invariant | `MISSING` |
| multi-time Record | full-text boundary | no QEC Record object is defined | raw law, temporal detector fold, logical bits, or Record distance | `MISSING` |
| finite-bond numerical truncation | pp. 3–4 and 5–6, exact-patch proof | the theoretically sufficient finite patch is contracted exactly | environment/bond truncation rule or numerical PEPS error certificate | `MISSING` |
| CAPEPS efficiency | full-text boundary | no Clifford-augmented PEPS method is defined | implementation, matched accuracy, runtime, or memory comparison | `MISSING` |

## 10. Project application

The source supplies a rigorous counter-boundary to blanket statements that all
PEPS contraction is intractable: a restricted class admits local-observable
approximation by exact contraction of a logarithmic-radius patch. That is the
only direct bridge available to the current CAPEPS question.

The following further steps would be project inferences, not paper claims:

- identifying a dynamically updated residual PEPS with an injective PEPS
  obeying the theorem after constant blocking;
- proving a uniformly gapped parent Hamiltonian for every prefix residual
  state arising through Clifford-frame updates, coherent rotations,
  measurement, and reset;
- controlling the condition numbers of the evolving residual tensors;
- replacing the theorem's exact patch contraction with a finite-bond PEPS
  environment approximation;
- lifting one local expectation's additive error to conditional-state fidelity
  or to total variation of a complete multi-round Record law;
- inferring any CAPEPS/full-PEPS runtime or peak-memory advantage.

Until those bridges are independently proved, Schwarz et al. cannot certify
record-faithful scalable CAPEPS execution. It can only calibrate the claim
language around conditional local-observable tractability.

## 11. Competing evidence and kill conditions

The source itself retains the principal contrary boundary: general PEPS
contraction is #P-complete, while the theorem excludes the hard construction
through injectivity and a constant uniform gap (p. 1; p. 6 hardness appendix,
citing Ref. 27). It also explicitly excludes non-injective/topological PEPS
and says the proof does not establish standard LTQO.

Any proposed application of the theorem is killed if at least one of the
following fails:

1. the relevant residual PEPS is injective after blocking only a constant
   number of tensors;
2. every required prefix parent Hamiltonian has a common nonvanishing lower
   gap \(\Delta_*\), rather than only the final PEPS having a gap;
3. the tensor condition numbers remain within the stated scaling regime;
4. the target is a constant-support local expectation rather than global
   fidelity, a conditional branch state, or a complete Record distribution;
5. the calculation exactly contracts the sufficient patch, or a separate
   theorem controls the numerical approximation that replaces it;
6. the hidden clustering constants are known if a numerical certificate,
   rather than asymptotic scaling, is claimed.

## 12. Source-local verdict

- read_status: `complete`
- evidence_status: `persisted`
- operation_replay_status: `complete_for_the_conditional_local_expectation_theorem`
- independent_admission_status: `passed`
- assigned_row_status:
  - conditional local-observable theorem: `closed_conditional`
  - injectivity/uniform-prefix-gap/conditioning/locality assumptions: `closed_as_assumptions`
  - generic or topological PEPS: `missing`
  - global state fidelity: `missing`
  - measurement/reset/Record law: `missing`
  - finite-bond PEPS truncation certificate: `missing`
  - CAPEPS implementation or efficiency comparison: `missing`

The candidate source-only note is safe for corpus admission only with the
conditional theorem boundary and all missing bridges above preserved.
