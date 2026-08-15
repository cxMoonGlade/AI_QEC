# McCloskey–Paternostro 1402.4639v3 — collision-model source audit

Status: source-only audit for the GCAPEPS finite-memory benchmark, 2026-07-29.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| system–ancilla coherent collision | Sec. I, Eqs. (1)–(2), PDF p. 2 | The system–ancilla collision is \(\cos\gamma I+i\sin\gamma\,\mathrm{SWAP}\). | It does not define a many-system PEPS ladder. | closed |
| ancilla–ancilla coherent collision | Sec. I, Eqs. (3)–(4), PDF p. 2 | The adjacent-ancilla collision is \(\cos\delta I+i\sin\delta\,\mathrm{SWAP}\). | It does not identify \(\delta\) with the distinct system–ancilla strength \(\gamma\). | closed |
| retained versus erased correlations | Sec. I.B, Eqs. (10)–(11), PDF p. 4 | Strategy 1 erases a system–ancilla correlation before it can be carried forward; Strategy 2 retains it through the next ancilla collision. | Neither strategy is a tensor-network truncation prescription. | closed |
| printed prior-pair argument | Sec. I, Eq. (8), PDF p. 3 | The displayed second distance is \(D(\rho^S_{2,n-1},\rho^S_{2,n-1})\). | The displayed term does not compare the two prior trajectories and is identically zero. | contradicted as printed |
| printed positive-increment selector | Sec. I, Eqs. (7)–(8), PDF p. 3 | Eq. (7) integrates only over intervals with positive trace-distance derivative. | Eq. (8) prints an unrestricted sum with no positive-increment selector, so it is not a literally usable discretization of Eq. (7). | missing as printed; supplied only by a cross-source audit derivation from BLP |
| stochastic draw-and-threshold rule | Sec. II.B and Fig. 6, PDF p. 6 | At each step a random variable is drawn and the system–environment collision occurs when the draw lies below a threshold in \([0,1]\). | The random-variable distribution is not specified, so the threshold is not source-identified numerically with a Bernoulli collision probability. | source rule closed; Bernoulli bridge missing source-locally |
| full-ancilla-swap stochastic finding | Sec. II.B and Fig. 6, PDF p. 6 | For the displayed \(\delta=\pi/2\) case, reducing collision occurrence changes the period of trace-distance oscillations while leaving their amplitude unchanged. | This parameter-specific finding is not a universal stochastic-collision law. | closed at the displayed parameter scope |
| monotonic entanglement claim | Figs. 3–6 and conclusions, PDF pp. 4–7 | Trace distance and correlation contributions can oscillate and decay. | The source does not establish monotonic entanglement growth with collision count. | missing source-locally |
| PEPS-bond claim | Complete source scope, PDF pp. 1–7 | The source analyzes reduced states, trace distance, and correlations. | It does not define or bound a PEPS virtual-bond dimension. | missing source-locally |
| truncation-error claim | Complete source scope, PDF pp. 1–7 | The collision evolution is formulated without a tensor-network truncation procedure. | It does not define a tensor-network truncation error. | missing source-locally |
| runtime claim | Complete source scope, PDF pp. 1–7 | The source reports physical observables rather than an algorithmic performance study. | It does not establish a runtime metric. | missing source-locally |

## Printed Eq. (8) anomalies

Visual inspection of PDF p. 3 establishes two independent defects in the
printed discrete expression.

1. Its second distance is
   \[
   D(\rho^S_{2,n-1},\rho^S_{2,n-1}),
   \]
   which is identically zero rather than a distance between the two prior
   trajectories.
2. Although Eq. (7) restricts its integral to intervals with
   \(\partial_tD>0\), Eq. (8) prints an unrestricted \(\sum_n\) with no
   positive-increment selector. Repairing only the arguments would therefore
   produce a telescoping sum, not total positive growth.

For one fixed input pair and a finite window, this audit discretizes the BLP
positive-growth construction as
\[
\mathcal N_{\rm pair}^{(R)}
=\sum_{n=1}^{R}\max\!\left[
0,\,
D(\rho^S_{1,n},\rho^S_{2,n})
-D(\rho^S_{1,n-1},\rho^S_{2,n-1})
\right].
\]
This is a cross-source project derivation from BLP Eqs. (1), (10)–(12), not a
silent correction or printed equation attributed to McCloskey–Paternostro.
Without maximization over all initial pairs it is a fixed-pair witness, not the
source's optimized \(\mathcal N\).

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| system qubit and ancilla \(E_j\) | apply \(\cos\gamma I+i\sin\gamma\,\mathrm{SWAP}\) | coherent two-qubit collision | updated joint state | Eqs. (1)–(2), PDF p. 2 | complete |
| adjacent ancillas \(E_j,E_{j+1}\) | apply \(\cos\delta I+i\sin\delta\,\mathrm{SWAP}\) | nearest-neighbor environmental transfer | memory can move to the next ancilla | Eqs. (3)–(4), PDF p. 2 | complete |
| post-collision joint state | erase or retain the relevant system–environment correlation before the next step | chosen strategy | two distinct reduced-system maps | Eqs. (10)–(11), PDF p. 4 | complete |
| two reduced-system trajectories | discretize BLP by evaluating only positive trace-distance increments | use the BLP-consistent pair of arguments and an explicit positive selector, neither of which is supplied by printed Eq. (8) | fixed-pair lower-bound backflow witness | cross-source audit derivation from BLP Eqs. (1), (10)–(12) | complete as a project derivation, not as a McCloskey equation |
| random draw and threshold | execute or skip a collision according to whether the draw is below the threshold | no distribution is supplied for the source's random variable | source-stated collision-occurrence indicator | Sec. II.B and Fig. 6, PDF p. 6 | complete at the draw-and-threshold rule; distribution bridge missing |
| declared uniform draw \(u_n\sim\mathrm{Uniform}[0,1]\) and project parameter \(p_{\rm event}\) | set \(m_n=\mathbf 1[u_n<p_{\rm event}]\) | uniformity is a project choice, not a fact established by the fixed paper | Bernoulli collision mask with occurrence probability \(p_{\rm event}\) | project choice; the paper specifies no draw distribution | not source-closed |
| source system–ancilla partial SWAP \(U_{S,j}(\gamma)\) | use \(\mathrm{SWAP}=(I+XX+YY+ZZ)/2\) and pairwise commutation to form \(e^{+i\gamma/2}e^{i\gamma XX/2}e^{i\gamma YY/2}e^{i\gamma ZZ/2}\) | project algebra; consuming API is declared as \(R_{PP}(\theta)=e^{-i\theta PP/2}\) | exact source unitary including global phase; API angles are \(\theta=-\gamma\) for each Pauli product | Eq. (1), PDF p. 2, plus this audit's Pauli-algebra derivation | complete project derivation |
| source ancilla–ancilla partial SWAP \(\widehat E_{j,j+1}(\delta)\) | use \(\mathrm{SWAP}=(I+XX+YY+ZZ)/2\) and pairwise commutation to form \(e^{+i\delta/2}e^{i\delta XX/2}e^{i\delta YY/2}e^{i\delta ZZ/2}\) | project algebra; consuming API is declared as \(R_{PP}(\theta)=e^{-i\theta PP/2}\) | exact source unitary including global phase; API angles are \(\theta=-\delta\) for each Pauli product | Eq. (3), PDF p. 2, plus this audit's Pauli-algebra derivation | complete project derivation |

## Project application

The source collision obeys \(U_{S,j}(\gamma)=e^{i\gamma\mathrm{SWAP}}\)
because \(\mathrm{SWAP}^2=I\). For qubits,
\(\mathrm{SWAP}=(I+XX+YY+ZZ)/2\), and the three nonidentity Pauli products
commute. The exact phase-bearing identity is
\[
U_{S,j}(\gamma)
=e^{+i\gamma/2}
 e^{i\gamma XX/2}
 e^{i\gamma YY/2}
 e^{i\gamma ZZ/2}.
\]
The same identity holds with the source's distinct ancilla strength \(\delta\)
for Eq. (3). If the consuming rotation API is
\(R_{PP}(\theta)=e^{-i\theta PP/2}\), each system–ancilla angle is
\(\theta=-\gamma\), and each ancilla–ancilla angle is \(\theta=-\delta\).
Dropping \(e^{+i\gamma/2}\) or \(e^{+i\delta/2}\) is allowed only behind an
explicit global-phase-insensitive comparison.

An independent complex128 audit replay at the non-special value
\(\gamma=0.37\) found zero pairwise-commutator residual and
\(1.25\times10^{-16}\) maximum absolute residual between the source's literal
partial-SWAP matrix and the phase-bearing Pauli product. This checks the audit
algebra, not any carrier implementation.

Ordinary Quimb can consume the literal four-by-four partial-SWAP matrix.
GCAPEPS can consume the three Pauli rotations only with the stated negative
API angles and a tested global-phase firewall.

The planned multi-system 2-by-\(L\) ladder is a bounded project
generalization. The paper's exact quantitative curves and thresholds do not
transfer to it. The source supports the collision primitive, the
correlation-retention mechanism, and only an unspecified-distribution
draw-and-threshold occurrence rule. A uniform draw that turns the threshold
into a Bernoulli occurrence probability is a declared project choice; its
distribution bridge is missing from this fixed source.

## Competing evidence and kill conditions

- The printed Eq. (8) must fail corruption tests for both its self-distance
  term and its missing positive-increment selector.
- A Bernoulli mask requires a declared uniform draw as a project choice. Its
  occurrence probability controls whether a collision gate is present in the
  frozen schedule; it is not a Pauli-twirl probability or a calibrated
  hardware error rate.
- Full swap is a special strong-memory point and can be Clifford; it is not a
  representative non-Clifford truncation stress point.
- Oscillatory source figures kill any upgrade of “more rounds” to a monotonic
  entanglement theorem.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: closed for the coherent primitives, correlation
  strategies, and source-stated draw-and-threshold rule; printed Eq. (8) has
  two independent defects, and the Bernoulli distribution bridge remains
  missing source-locally
