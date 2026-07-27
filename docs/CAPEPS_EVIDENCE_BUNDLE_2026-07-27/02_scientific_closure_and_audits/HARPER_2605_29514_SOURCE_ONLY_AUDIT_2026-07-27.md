# Harper et al. arXiv:2605.29514v1 — source-only audit

Date: 2026-07-27
Status: `SOURCE_ONLY_REVIEWED`
Independent reviewer: `independent_harper_2605_source_only_review_2026_07_27`
Source: arXiv:2605.29514v1
Scope: source claims, equations, figures, operation replay, and source-local absences only

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

### 3.2 Noise channel and Pauli twirl

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

## 4. Source-local anomalies and limitations

1. Equation (4) prints \(e^{+i\theta ZZ}\), while the circuit prints
   CNOT--\(R_Z(\theta/2)\)--CNOT without defining \(R_Z\). Under the common
   half-angle convention these differ in sign and by a factor of four in the
   exponent; their intended equivalence is `MISSING/AMBIGUOUS`.
2. Table I's \(\theta=10^{-3}\), Eq. (5), the Sec. III.B order-of-magnitude
   example, and the Sec. V.A values do not form one numerically consistent
   parameter set. The source does not reconcile \(10^{-3}\), \(10^{-2}\), and
   \(0.0225\).
3. Equation (8) sums to \(\chi-1\), while the prose calls \(\chi\) the bond
   dimension and caps it at \(\chi_{\max}\); the off-by-one convention is not
   explained.
4. The abstract says that inclusion of coherence lowers the threshold. The
   detailed result in Sec. V instead separates the effects: crosstalk lowers the
   threshold from about \(1\%\) to \(0.8\%\), while coherence has no
   statistically significant additional threshold effect. Source use must keep
   the detailed qualification.
5. Table I assigns reset error rate \(p_R=2p\) and measurement error rate
   \(p_M=5p\), but the paper does not specify an outcome-resolved reset map,
   branch-state invariant, or reset correctness observable.
6. The paper states that projective measurement is implemented through a Pauli
   sum, but it does not give Born branch masses, prefix masses, complete
   enumeration, or population-law certification.
7. The source reports logical-error behaviour, not conditional-state fidelity,
   raw-law TV, detector/observable Record-TV, or complete classical–quantum
   instrument distance.
8. The source does not report a full-process runtime or peak-memory comparison
   against full MPS, full PEPS, PEPS residuals, dense reference, or a twirled
   tableau route at matched accuracy.
9. PEPS and tree tensor networks appear only as possible future layouts in the
   conclusion.
10. The PyMatching decoder uses the Pauli-twirled error model even when the
    simulated forward dynamics retain coherence.

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
| Clifford and non-Clifford update direction | `CLOSED` |
| printed Eq. (4) and CNOT--\(R_Z\)--CNOT equivalence | `MISSING_AMBIGUOUS` |
| one internally consistent \(\theta\) parameter set | `MISSING_INCONSISTENT` |
| Eq. (8) \(\chi-1\) indexing explanation | `MISSING` |
| projective-measurement pull-through at the stated level | `CLOSED` |
| explicit reset error rate | `CLOSED_AS_MODEL_PARAMETER` |
| explicit reset instrument or reset-state certificate | `MISSING` |
| complete raw or detector/observable Record law | `MISSING` |
| MPS truncation method and reported bias direction | `CLOSED_FOR_REPORTED_WORKLOAD` |
| PEPS residual implementation | `FUTURE_WORK_ONLY` |
| matched-accuracy CAPEPS/full-PEPS resource result | `MISSING` |

The source closes an important adjacent-work row: coherent, repeated
surface-code syndrome extraction has already been simulated with a
Clifford-frame/MPS-residual method. It does not close the PEPS residual,
record-faithfulness, or matched-efficiency claims.
