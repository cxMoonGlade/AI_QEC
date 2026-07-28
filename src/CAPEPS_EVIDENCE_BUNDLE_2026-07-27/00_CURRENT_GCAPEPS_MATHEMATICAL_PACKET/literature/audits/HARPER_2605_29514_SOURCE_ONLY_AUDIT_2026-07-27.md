# Harper et al. arXiv:2605.29514v1 — source-only audit

Date: 2026-07-27
Status: `SOURCE_ONLY_REVIEWED`
Independent reviewer: `/root/review_masot_source` (`PASS` on round-2 admission review)
First review basis: `docs/simulator_validation/HARPER_2605_29514_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`
Round-2 review basis: `docs/simulator_validation/HARPER_2605_29514_INDEPENDENT_SOURCE_REREVIEW_ROUND2_2026-07-27.md`
Round-2 review SHA-256: `1e9c7bcebc7b8763a23ea86c0c656b7092fe3f26013623af652ab85a9cfb5781`
Source: arXiv:2605.29514v1
Scope: source claims, equations, figures, operation replay, and source-local absences only

The previous `SOURCE_ONLY_REVIEWED` status named a reviewer, but the repository
contained no durable independent-review report for that admission, so that
earlier admission was withdrawn before this repair. The main agent read all eight pages and visually
inspected PDF pages 1–7 on 2026-07-27. A fresh independent reviewer then read
and visually inspected all eight pages and rejected the candidate packet for
omitted formula anomalies, a missing mechanism-to-observable bridge, an omitted
null result, and bundled locators. Those defects were repaired in the candidate
note and this audit. A fresh source-first round-2 review then passed all 42
evidence records and the artifact-verified schema preflight, so this packet is
admitted only at the bounded source-only scope stated below.

## 1. Pinned source

| field | value |
|---|---|
| title | *Non-Clifford Crosstalk Noise in Surface Codes Using Hybrid Stabilizer-Tensor Network Methods* |
| authors | Ben Harper, Azar C. Nakhl, Martin Sevior, Muhammad Usman |
| version | arXiv:2605.29514v1, submitted 28 May 2026 |
| source URI | `https://arxiv.org/abs/2605.29514v1` |
| source artifact | `docs/papers/2605.29514v1.pdf` |
| SHA-256 | `c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd` |
| extent | 8 pages, 6 figures |

The versioned arXiv PDF was read in full. PDF pages 1–7 were rendered and
visually inspected. Page 8 contains the remainder of the bibliography and was
checked from the pinned PDF text. Formula, table, circuit, and plotted-curve
claims below use the printed PDF page number.

## 2. Source question and answer

The source asks how coherent nearest-neighbour \(ZZ\) crosstalk affects
rotated-surface-code syndrome extraction when the coherent channel is simulated
without replacing it by its Pauli twirl.

Its method uses a hybrid representation

\[
|\psi\rangle=C|\mathrm{MPS}\rangle,
\]

where the ideal Clifford circuit is accumulated in \(C\), while the MPS carries
the non-Clifford perturbation. The reported experiment simulates distances
\(d=3,5,7,9\), repeats syndrome extraction for \(d\) rounds, caps the MPS bond at
\(\chi_{\max}=32\), and compares coherent and Pauli-twirled crosstalk through a
logical-error observable.

This source does not implement a PEPS residual, a complete raw-outcome law, a
detector/observable Record fold, a branch-mass ledger, or a matched-accuracy
full-PEPS resource comparison.

## 3. Formula and operation replay

### 3.1 Rotated-surface-code circuit

Figure 1 and Sec. II place data qubits on square-lattice vertices and ancillas
on faces. The printed circuits prepare an ancilla in \(|0\rangle\), use ordered
CNOTs to extract a weight-four \(Z\)- or \(X\)-type check, and measure the
ancilla. Boundary checks have weight two. The source states that this syndrome
extraction is repeated for \(d\) rounds.

Replay boundary:

- the paper specifies the local check circuits and round count;
- it does not publish absolute measurement-column indices, initial/terminal
  detector anchors, logical-observable XOR rows, or a complete raw-to-Record
  map.

Equation (1) defines \(P_L\) after syndrome-associated logical angles
\(\theta_i\) are available. The source does not specify how the sampled
syndrome, the PTA-derived PyMatching correction, and the resulting coherent
logical channel are converted into each \(\theta_i\). The
correction-to-logical-angle step is therefore not independently replayable.

### 3.2 Noise channel and Pauli twirl

The baseline one-qubit channel in Eq. (2) is printed with coefficient
\(p_1/3\), followed by a sentence that places its index in
\(\{I,X,Y,Z\}\). Read literally with the identity included, its trace is
\(1+p_1/3\), not one. Excluding \(I\) is a plausible intended repair, but the
source does not state it. Equation (3), by contrast, explicitly excludes
\((I,I)\) from its 15 two-qubit Pauli terms and is normalized under that
printed exclusion.

The coherent crosstalk channel is

\[
\epsilon(\rho)=
e^{i\theta Z_1Z_2}\rho e^{-i\theta Z_1Z_2},
\qquad
\theta=J_{ZZ}t_g.
\]

The source separately prints a CNOT--\(R_Z(\theta/2)\)--CNOT circuit but does
not define its \(R_Z\) convention. Under the common convention
\(R_Z(\varphi)=e^{-i\varphi Z/2}\), that circuit evaluates to
\(e^{-i\theta Z_1Z_2/4}\), not the displayed \(e^{+i\theta Z_1Z_2}\).
The relation between the printed channel and circuit is therefore
`MISSING/AMBIGUOUS`; this audit does not silently choose a convention.

The source's parameter values are also not reconciled internally. Table I
fixes \(\theta=10^{-3}\), Eq. (5) states \(\theta=J_{ZZ}t_g\), Sec. III.B's
order-of-magnitude example gives \(100\,\mathrm{kHz}\times100\,\mathrm{ns}
=10^{-2}\), and Sec. V.A gives
\(150\,\mathrm{kHz}\times150\,\mathrm{ns}=0.0225\). These printed values are
recorded separately rather than treated as one consistent parameter set.

The source's printed Pauli-twirled channel is
\[
\epsilon_{\mathrm{twirl}}(\rho)
=\bigl(1-\sin^2\theta\bigr)\rho
+\sin^2\theta\,(Z\otimes Z)\rho(Z\otimes Z).
\]
Expanding the displayed Eq. (4) unitary, rather than the ambiguous circuit,
reproduces those diagonal weights after the coherent cross terms are removed.
The twirl is a different stochastic channel, not a lower-precision execution of the same coherent trajectory.

### 3.3 Hybrid state update

The opening of Sec. IV explicitly identifies GCAMPS as the simulation library
used for the reported experiment. It supplies no version, commit, archived
executable artifact, or source-code locator for that run.

Equation (7) defines

\[
|\psi\rangle=C|\mathrm{MPS}\rangle.
\]

For a physical Clifford \(G\), the source uses

\[
G|\psi\rangle=GC|\mathrm{MPS}\rangle=C'|\mathrm{MPS}\rangle.
\]

For a non-Clifford operation expanded as a Pauli sum, it writes

\[
U|\psi\rangle
=\sum_iP_iC|\mathrm{MPS}\rangle
=C\sum_i\widetilde P_i|\mathrm{MPS}\rangle
=C|\mathrm{MPS}'\rangle.
\]

The prose names this operation \(T\), whereas the display uses \(U\). The
display also omits the coefficients and normalization of the generic Pauli
expansion. It is therefore a formal pull-through identity at the printed level,
not a complete executable decomposition rule.

The printed text explicitly warns that conjugation through \(C\) can turn a
physically local Pauli word into a higher-weight operation on the MPS. It says
projective measurement is treated analogously by commuting a Pauli sum through
\(C\) and applying it to the tensor network.

In the paper's QEC interpretation, \(C\) is the ideal Clifford code circuit and
the MPS stores the perturbing non-Clifford error. On measurement, the source
states that the MPS error collapses to a Pauli error in the Clifford tableau.
It does not print the outcome-resolved Kraus operator, Born branch probability,
normalization rule, or reset transaction.

### 3.4 Optimizer decision

The source does not use magic-state injection or Clifford optimization. It
states that the number of non-Clifford gates would require too many magic
ancillas and that the cost of Clifford optimization outweighed the benefit from
reducing MPS bond dimension. This is a source-specific negative result for the
reported MPS surface-code workload, not a theorem about all hybrid tensor
networks.

### 3.5 Truncation

Equation (8) writes a Schmidt decomposition across the central MPS cut,

\[
|\psi\rangle=\sum_{i=1}^{\chi-1}\lambda_i|i_L\rangle|i_R\rangle,
\]

and the text says it limits bond dimension \(\chi\) to \(\chi_{\max}\) by
discarding the smallest singular-value terms. The paper does not explain why
the printed sum ends at \(\chi-1\) while the prose calls \(\chi\) the bond
dimension. Figures 2–3 report rapid decay and convergence for the studied
workload. The source also states that aggressive truncation lowers the measured
logical-error rate because the largest MPS component is the no-crosstalk state,
so it interprets the reported logical-error values as lower bounds. All later
figures use \(\chi_{\max}=32\).

The bound following Eq. (8) uses uppercase \(N\) without defining it in the
truncation subsection. Equation (1) used uppercase \(N\) for sample count,
while the Fig. 2 caption uses lowercase \(n\) for physical-qubit count. The
intended size symbol in \(\chi_{\max}\le2^{N/2}\) is therefore ambiguous.

The paper does not derive a complete-state fidelity bound, a conditional-state
bound, or a raw/Record total-variation bound from the retained Schmidt values.

### 3.6 Reported comparison

The Fig. 4 data points average \(10^5\) samples. In that comparison, adding
crosstalk lowers the threshold from about \(1\%\) to \(0.8\%\). The text then
states that adding coherence increases sub-threshold logical error further but
does not have a statistically significant additional effect on the threshold.

Equation (9) introduces a random-sign model

\[
\theta_i\in\{\theta,-\theta\}.
\]

Because \(\sin^2\theta=\sin^2(-\theta)\), the fixed-sign and random-sign
coherent models have the same Pauli twirl. Figures 5–6 nevertheless report
different sub-threshold logical-error behaviour. This is evidence that the
twirled channel is not a sufficient statistic for the paper's logical-error
observable in the studied regime.

The contrary/null result must also be retained: the Fig. 5 caption says that
the random-sign coherent model's logical-error rates are identical to the PTA
despite the model remaining coherent. The source therefore supports a
distribution-dependent failure of the twirl, not a claim that every coherent
model differs from its Pauli twirl.

## 4. Source-local anomalies and limitations

1. Equation (2) includes \(I\) in its stated one-qubit Pauli index set despite
   the \(p_1/3\) coefficient; read literally, the printed map is not
   trace-preserving.
2. Equation (4) prints \(e^{+i\theta ZZ}\), while the circuit prints
   CNOT--\(R_Z(\theta/2)\)--CNOT without defining \(R_Z\). Under the common
   half-angle convention these differ in sign and by a factor of four.
3. Table I, Eq. (5), the Sec. III.B example, and Sec. V.A do not form one
   numerically consistent \(\theta\) parameter set: the printed values imply
   \(10^{-3}\), \(10^{-2}\), and \(0.0225\).
4. The non-Clifford paragraph switches from \(T\) to \(U\), and its formal
   Pauli sum omits coefficients and normalization.
5. Equation (8) sums to \(\chi-1\), and the following size bound uses an
   undefined uppercase \(N\) where the surrounding source also uses lowercase
   \(n\) for qubit count.
6. The source does not supply the transformation from a sampled syndrome and
   decoder correction to the logical angle required by Eq. (1).
7. The abstract's threshold wording is stronger than Sec. V.A, which says that
   coherence has no statistically significant additional threshold effect
   beyond the threshold reduction caused by crosstalk.
8. Table I supplies reset and measurement error rates, but no outcome-resolved
   reset transaction or reset-state invariant.
9. Projective measurement is described through a Pauli sum, but the source
   gives no Born branch masses, conditional-state normalization, prefix masses,
   or branch-completeness test.
10. The source reports logical-error behaviour, not a complete raw law,
    conditional-state fidelity, detector/observable Record-TV, or complete
    classical--quantum instrument distance.
11. Fig. 5 reports that the random-sign coherent model agrees with its PTA;
    this null result limits any blanket anti-twirl conclusion.
12. No matched-accuracy runtime, peak-memory, or throughput comparison is
    reported against full MPS, full PEPS, PEPS residuals, dense reference, or a
    twirled tableau route.
13. PEPS and tree tensor networks appear only as possible future layouts.
14. PyMatching uses the Pauli-twirled error model even when the simulated
    forward dynamics retain coherence.
15. The source names GCAMPS but supplies no version, commit, archived executable,
    or source-code locator for the reported run.

## 5. Disconfirmation retained for CAPEPS-related reading

The following source facts, plus one labeled project inference, oppose an
automatic CAPEPS-efficiency inference:

- a physically local Pauli word may become high weight after pull-through;
- because projective measurement also uses a pulled-through Pauli sum, frequent
  measurements may make nonlocal residual work costly `[project inference]`;
- Clifford-optimizer cost exceeded its bond benefit in the reported workload;
- MPS truncation can suppress rare-error contributions and bias the logical
  observable downward;
- the paper proposes PEPS only as future work and supplies no PEPS resource
  result.

These are source-local limitations. Whether a separately defined
\(C|\mathrm{PEPS}\rangle\) method is faster or slower than full PEPS remains a
new empirical question.

## 6. Source-only verdict

| row | verdict |
|---|---|
| repeated rotated-surface-code use of \(C|\mathrm{MPS}\rangle\) | `CLOSED` |
| explicit GCAMPS library identity | `CLOSED` |
| GCAMPS executable version or commit | `MISSING` |
| printed one-qubit depolarizing map | `AMBIGUOUS_NOT_TRACE_PRESERVING_AS_PRINTED` |
| Clifford and non-Clifford update direction | `CLOSED` |
| executable generic non-Clifford Pauli coefficients | `MISSING` |
| printed Eq. (4) and CNOT--\(R_Z\)--CNOT equivalence | `MISSING_AMBIGUOUS` |
| one internally consistent \(\theta\) parameter set | `MISSING_INCONSISTENT` |
| Eq. (8) \(\chi-1\) indexing explanation | `MISSING` |
| Eq. (8) system-size symbol | `MISSING_AMBIGUOUS` |
| syndrome/correction-to-logical-angle construction | `MISSING` |
| projective-measurement pull-through at the stated level | `CLOSED` |
| explicit reset error rate | `CLOSED_AS_MODEL_PARAMETER` |
| explicit reset instrument or reset-state certificate | `MISSING` |
| complete raw or detector/observable Record law | `MISSING` |
| MPS truncation method and reported bias direction | `CLOSED_FOR_REPORTED_WORKLOAD` |
| random-sign coherent/PTA agreement in Fig. 5 | `CLOSED_CONTRARY_RESULT_RETAINED` |
| PEPS residual implementation | `FUTURE_WORK_ONLY` |
| matched-accuracy CAPEPS/full-PEPS resource result | `MISSING` |

The source closes an important adjacent-work row: coherent, repeated
surface-code syndrome extraction has already been simulated with a
Clifford-frame/MPS-residual method. It does not close the PEPS residual,
record-faithfulness, or matched-efficiency claims.
