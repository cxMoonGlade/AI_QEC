# Bravyi, Gosset, and Liu arXiv:2112.08499v2 — source-only audit

Date: 2026-07-27

Status: `DRAFT_PENDING_INDEPENDENT_SOURCE_ONLY_REVIEW`

Independent admission reviewer: `pending`

Scope: exact and approximate computational-basis sampling from amplitude
queries, tensor-network and stabilizer-rank applications, adaptive-circuit and
surface-code-MBQC scope, ground-state sampler, and source-local absences

The complete 17-page source was read in order, including the Supplemental
Material. PDF pages 1--5, 10--12, and 16--17 were rendered and visually
inspected at the load-bearing algorithms, equations, table, theorems, and
scope boundaries. Text extraction was used for traversal only. This packet is
a source reconstruction, not an admission review.

## 1. Pinned source

| field | value |
|---|---|
| title | *How to simulate quantum measurement without computing marginals* |
| authors | Sergey Bravyi, David Gosset, Yinchen Liu |
| version | arXiv:2112.08499v2, visible stamp 6 January 2022 |
| source URI | `https://arxiv.org/abs/2112.08499v2` |
| source artifact | `docs/papers/2112.08499v2.pdf` |
| SHA-256 | `4743d2f0ed7de44f0da83ca875fb69dd15378cecfb54ef368da93d81580c68c6` |
| extent | 17 pages, including Supplemental Material |

## 2. Source question and bounded answer

The paper asks how to sample a standard-basis outcome
\(x\sim |\langle x|\psi\rangle|^2\) without evaluating the growing marginals
used by the usual qubit-by-qubit chain rule.

For a circuit \(U=U_m\cdots U_1\) of \(k\)-local unitary gates, Algorithm 2
maintains a classical bit string and, after gate \(U_t\), resamples only the
bits in the support of that gate using output probabilities of the prefix
circuit. Exact prefix amplitudes therefore give an exact final sample with at
most \(m2^k\) probability evaluations. The proof is distributional: the
classical sampler distribution \(Q_t\) equals the prefix output distribution
\(P_t\) after every step.

This result is important prior art for a marginal-free Born sampler and for
using tensor-network or low-rank stabilizer amplitude routines as a backend.
It is not a representation of a post-measurement conditional quantum state and
does not define reset, a repeated syndrome-extraction instrument, or a
detector/observable Record fold.

## 3. Gate-by-gate operation replay

For prefix \(t\), define

\[
P_t(x)=|\langle x|U_t\cdots U_1|0^n\rangle|^2.
\]

Given the current bit string \(x\), let \(A\) be the complement of the support
of \(U_t\), and let \(S\) contain the strings agreeing with \(x\) on \(A\).
Algorithm 2 resamples \(x\in S\) with probability

\[
\frac{P_t(x)}{\sum_{y\in S}P_t(y)}.
\]

The denominator is a local normalization over at most \(2^k\) strings, not the
large prefix marginal required by Algorithm 1. Since \(U_t\) is trivial on
\(A\), the \(A\)-marginal of \(P_{t-1}\) equals that of \(P_t\). Induction then
gives \(Q_t=P_t\). This is the exact invariant carried by the algorithm.

For CNOT plus arbitrary single-qubit gates, the source updates the sampled bits
deterministically at a CNOT and needs at most \(2m\) probability evaluations.
Diagonal gates can be skipped because they do not change \(P_t(x)\).

The adaptive-circuit extension is bounded by footnote 28: once a qubit is
measured, later gates act trivially on it, and a later gate may be classically
controlled by earlier outcomes. This supports adaptive output sampling, but it
does not supply a reset/re-preparation transaction or a general outcome-resolved
quantum channel.

## 4. Approximation error and what it does not certify

The robustness lemma assumes approximate prefix states \(|\phi_t\rangle\) with
global vector-norm errors

\[
\|\phi_t-U_t\cdots U_1|0^n\rangle\|\leq \epsilon_t.
\]

For the modified gate-by-gate sampler, Eq. (3) gives the source's \(L_1\)
bound

\[
\|Q-P_m\|_1\leq 16\sum_{t=1}^{m-1}\epsilon_t.
\]

This is a useful bridge from independently controlled global prefix-state
errors to a final classical output law. It is not, by itself, a method for
obtaining the \(\epsilon_t\) from local PEPS truncations, approximate
environments, or selective branch compression. The paper writes an \(L_1\)
norm; under the common convention, total variation is one half of that norm.

## 5. Tensor-network and stabilizer-rank applications

The source argues that a marginal contraction can resemble a doubled-depth
network, whereas Algorithm 2 needs prefix amplitudes. Its CoTenGra example uses
a 49-qubit, depth-16 circuit on a \(7\times7\) grid and imposes maximum
intermediate-tensor-size constraints. Tables I--II report optimizer-estimated
FLOP counts, not contractions that were executed. The source also reports that
one dynamic-slicing optimization run involving both algorithms took about
three days on 60 CPU cores.

The result is workload- and optimizer-specific. It is not a theorem that
gate-by-gate sampling is faster for every tensor-network geometry, and it does
not report a measured peak-memory or CAPEPS/full-PEPS comparison.

For a Clifford circuit with \(\ell\) inserted \(T\) gates, the paper combines
Algorithm 2 with a stabilizer decomposition. Exact amplitudes cost
\(\mathrm{poly}(n)\chi\), so the exact sampler is linear in the stabilizer rank
of the magic resource rather than quadratic as in the cited earlier
qubit-by-qubit route. The Supplemental Material extends the robustness lemma to
sum-over-Cliffords approximations and records the stated cost formulas in
Eqs. (23)--(30).

## 6. Surface-code MBQC is not syndrome extraction

The Supplemental Material defines \(|\psi_G\rangle\) for a planar graph as the
uniform superposition of cycles, Eq. (31). Algorithm 3 initializes by sampling
that stabilizer resource state and then applies the gate-by-gate update for a
sequence of adaptive one-qubit measurement bases.

The required surface-code amplitude problem is reducible to a planar Ising
partition function. The source gives runtime \(O(n^4T)\) for a general planar
graph, where \(T\) bounds evaluation of the adaptive basis rule, and notes an
\(O(n^3T)\) specialization for the square lattice. Theorem 2 shows that the
corresponding unrestricted surface-code marginal problem is \(\#P\)-hard.

The hardness statement is order-sensitive. For regular non-adaptive
measurement, one may reorder measurements to satisfy the connectivity
constraint and use the earlier method. More importantly for source scope,
this is MBQC with a surface-code resource state; it is not a noisy surface-code
memory experiment, syndrome extraction with measurement and reset, decoder
Record generation, or coherent XZZX circuit simulation.

## 7. Ground-state sampler

The second algorithm concerns a unique ground state of a Hamiltonian whose
matrix elements connect bit strings at Hamming distance at most fixed
\(k=O(1)\), with spectral gap \(\gamma>0\). Given an initial supported string
with non-negligible \(\pi(x_{\mathrm{in}})\) and amplitude-ratio access, the
Metropolis--Hastings chain uses local bit-flip proposals and acceptance
probabilities from \(\pi(y)/\pi(x)\).

The stated call scaling depends on the sensitivity parameter \(s\), inverse
gap, and initial probability,

\[
T\sim \frac{n^k s}{\gamma}
\log\!\left(\frac{1}{\pi(x_{\mathrm{in}})\epsilon}\right).
\]

Pages 4--5 prove the mixing bound through the Markov-chain spectral gap. The
Supplemental Material proves \(s\leq\max_y\langle y|H|y\rangle-E_0\) for a
stoquastic Hamiltonian and defines a frustration-free “magic ratio” family for
which the required ratios and \(s\leq m\) can be controlled. These are
conditional results, not a generic efficient sampler for arbitrary gapped
Hamiltonians.

## 8. Assigned closure rows

| row | exact source location | bounded source result | status |
|---|---|---|---|
| exact marginal-free circuit sampling | Algorithm 2 and Eq. (2), PDF p. 2 | Exact prefix probabilities give \(Q_t=P_t\) and at most \(m2^k\) probability evaluations. | `closed_at_exact_amplitude_oracle` |
| adaptive intermediate measurements | PDF p. 2 and footnote 28 on p. 6 | Classical feed-forward is supported under the stated measured-qubit-is-never-acted-on-again convention. | `closed_at_source_convention` |
| approximate-output bound | Lemma 1, Eq. (3), PDF p. 4; proof pp. 7--8 | Global prefix-state norm errors imply the printed final \(L_1\) bound. | `closed_at_assumed_prefix_errors` |
| tensor-network comparison | PDF p. 3, Table I; Supplemental pp. 9--10, Table II | CoTenGra optimizer estimates favor the gate-by-gate route on the displayed sliced 49-qubit workload. | `closed_at_estimated_workload` |
| low-rank stabilizer use | PDF p. 3; Supplemental pp. 8--9 | The amplitude sampler reduces exact rank dependence and supports the source's approximate sum-over-Cliffords formulas. | `closed_at_source_assumptions` |
| surface-code MBQC | PDF pp. 3--4; Supplemental pp. 10--12, Algorithm 3 and Theorem 2 | Any planar-graph temporal order is efficiently sampled from amplitude queries; unrestricted marginals are \(\#P\)-hard. | `closed_for_mbqc_only` |
| measurement--reset--Record instrument | complete source scope | No reset transaction, QEC raw-history law, prefix branch-mass ledger, or detector/observable fold is defined. | `missing` |
| CAPEPS/full-PEPS efficiency | complete source scope | No PEPS residual, Clifford frame, matched full-PEPS arm, Record-TV, conditional fidelity, or measured peak-memory comparison is present. | `missing` |

## 9. Source-local cautions

1. “Without computing marginals” still uses a normalization over the at most
   \(2^k\) configurations affected by one gate; it avoids the large marginals
   of Algorithm 1.
2. Equation (3) is printed as an \(L_1\) distance. Any project use of standard
   total variation must include the factor \(1/2\).
3. Tables I--II are contraction-tree FLOP estimates. They are not measured
   contraction runtimes, output accuracies, or peak-memory observations.
4. Surface-code MBQC uses a resource-state cycle superposition and adaptive
   one-qubit measurement bases. Its name does not turn it into a surface-code
   syndrome-extraction or error-correction experiment.
5. The robustness lemma assumes global prefix-state error values; it does not
   derive them from a finite tensor-network bond or environment approximation.

## 10. Bounded project application and kill conditions

This source blocks any broad statement that marginal-free exact Born sampling
from tensor-network or low-rank-stabilizer amplitude queries is new. It also
requires any measurement contribution to distinguish classical output-law
sampling from preservation of an outcome-resolved quantum instrument.

The source may not be used to infer:

- a measurement--reset--Record implementation;
- equality of conditional quantum states after selective measurements;
- a finite-PEPS truncation-to-Record error certificate;
- a Clifford-frame/PEPS-residual representation;
- a noisy XZZX syndrome circuit or decoder Record;
- a universal tensor-network speedup; or
- a matched CAPEPS/full-PEPS runtime, peak-memory, bond, and accuracy result.

## 11. Source-local verdict

- `read_status: complete`
- `evidence_status: persisted_pending_independent_source_only_review`
- marginal-free exact circuit sampler: `closed_at_exact_amplitude_oracle`
- adaptive measurement output sampling: `closed_at_source_convention`
- global-prefix-error to final-law bound: `closed_at_assumed_errors`
- surface-code result: `closed_for_mbqc_resource_state_only`
- post-measurement conditional state: `missing`
- reset and repeated QEC Record: `missing`
- CAPEPS and matched full-PEPS comparison: `missing`

Admission requires a fresh independent full-source semantic review, a strict
artifact-verifying preflight of the companion note, and controlled promotion.
