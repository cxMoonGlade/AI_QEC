# BLP / McCloskey–Paternostro non-Markovianity — independent source-only review

Date: 2026-07-29  
Review scope: fixed local PDFs plus the two candidate source notes and their named audit packets only  
Verdict: **REQUIRED REPAIRS**

This review does not accept any candidate-note, audit-packet, project, or implementation conclusion as
evidence. Paper claims below were checked against the fixed PDF itself. Project-application text was
checked only for whether it is correctly separated from, and not falsely attributed to, the paper.

## Objects reviewed

| object | independently observed identity |
|---|---|
| `docs/papers/0908.0238v2.pdf` | PDF 1.4, 4 pages, valid `%PDF-` head and `%%EOF` tail, SHA-256 `9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553` |
| BLP candidate note | SHA-256 `dc17b482aa85aaca3c5ec271e37b727423bad0f5a0ce40c6f9974605c8e3a5f3`; its recorded PDF hash is exact |
| BLP candidate audit | SHA-256 `91d00a1ebc629786f0efa125e24b01dab7cf92fb93979d74502df7af8a3c1dd6`; the note's `audit_packet_sha256` is exact |
| `docs/papers/1402.4639v3.pdf` | PDF 1.5, 7 pages, valid `%PDF-` head and `%%EOF` tail, SHA-256 `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` |
| McCloskey–Paternostro candidate note | SHA-256 `adeba116da0ab9d542ebeb5bbcfcd2303e9ad62347139ea4774c69376d0b8603`; its recorded PDF hash is exact |
| McCloskey–Paternostro candidate audit | SHA-256 `f0d1831a0cf173e8595f0c0b1b6e7f9f4c334af201014cb838bc93f5df65833c`; the note's `audit_packet_sha256` is exact |

The BLP PDF visibly carries `arXiv:0908.0238v2 [quant-ph] 5 Jan 2010`, while its title page says
`Dated: October 26, 2018`. The McCloskey–Paternostro PDF visibly carries
`arXiv:1402.4639v3 [quant-ph] 26 May 2014`, while its title page says
`Dated: November 27, 2021`. The candidate notes record the arXiv version dates but do not preserve
these artifact-internal date pairs.

Neither fixed PDF contains the candidate source-identity locator described as a “journal reference”
for the paper itself. In particular, the fixed BLP PDF does not itself state that it is the
“published-version preprint” of PRL 103, 210401, and the fixed McCloskey–Paternostro PDF does not
itself state that it was published as PRA 89, 052120. Those facts may be true, but they are not
established by the fixed source set used for this review.

## Independent adjudication of McCloskey Eq. (8)

Visual inspection of PDF page 3 confirms that Eq. (8) is printed as

\[
\mathcal N=\max\sum_n\left[
D(\rho^S_{1,n},\rho^S_{2,n})
-D(\rho^S_{2,n-1},\rho^S_{2,n-1})
\right].
\]

The second distance is therefore exactly zero. This is not a defensible alternative convention: it
is inconsistent with Eq. (7), which measures positive changes in the distance between the two
trajectories. The candidate is correct that the displayed second distance is defective.

There is a second, independently visible defect or omission that the candidate does not record as
such. Eq. (7) integrates only where \(\partial_tD>0\), but the displayed Eq. (8) has an unrestricted
\(\sum_n\) and no positive-increment selector. Merely repairing the first argument of the second
distance would make the unrestricted sum telescope; it would not compute total positive growth.
Thus the printed equation is defective in both:

1. the first argument of the second distance; and
2. the absent restriction to positive discrete increments.

For one fixed input pair and a finite window, the audit's project-derived expression

\[
\mathcal N_{\mathrm{pair}}^{(R)}
=\sum_{n=1}^{R}\max\!\left(0,
D(\rho^S_{1,n},\rho^S_{2,n})
-D(\rho^S_{1,n-1},\rho^S_{2,n-1})\right)
\]

is mathematically consistent with discretizing BLP's positive-growth construction. It is not an
equation printed or derived by McCloskey–Paternostro, and without maximization over initial pairs it
is not their Eq. (7) measure \(\mathcal N\). The candidate audit mostly preserves this distinction
by naming it \(\mathcal N_{\rm pair}^{(R)}\), but the source note's Eq. (8) gap must record both
printed defects atomically.

## Independent replay of the partial-SWAP decomposition

McCloskey–Paternostro Eq. (1) defines

\[
U_{S,j}(\gamma)=\cos\gamma\,I+i\sin\gamma\,S.
\]

Because \(S^2=I\), this is exactly \(e^{i\gamma S}\). For qubits,

\[
S=\frac{I+X\!\otimes X+Y\!\otimes Y+Z\!\otimes Z}{2},
\]

and \(XX\), \(YY\), and \(ZZ\) commute pairwise. Therefore the exact phase-bearing identity is

\[
U_{S,j}(\gamma)
=e^{+i\gamma/2}
 e^{i\gamma XX/2}
 e^{i\gamma YY/2}
 e^{i\gamma ZZ/2}.
\]

Equivalently, the product of the three Pauli exponentials is
\(e^{-i\gamma/2}U_{S,j}(\gamma)\). The candidate audit's “up to a global phase” decomposition is
correct, and the omitted exact phase has sign \(+\gamma/2\) when it multiplies the product to recover
the source unitary. If a gate API defines \(R_{PP}(\theta)=e^{-i\theta PP/2}\), the corresponding
rotation angle is \(\theta=-\gamma\), not \(+\gamma\). The same algebra applies with \(\delta\) to
Eq. (3).

An independent complex128 matrix replay gave exact structural equality for the SWAP Pauli identity,
zero pairwise commutators, and maximum residual \(2.3\times10^{-16}\) for the phase-bearing
decomposition at a non-special test angle. This is an algebra check, not evidence for any project
implementation.

## BLP note: fact-by-fact review

| Fact ID | source / locator check | atomicity and semantic result |
|---|---|---|
| `blp-source-identity` | arXiv ID, v2 stamp, title, authors, and 4-page count are correct | **Repair:** the journal-publication assertion and “journal reference” locator do not resolve in the fixed PDF; preserve both visible date lines without explaining their discrepancy |
| `blp-selection-scope` | abstract and page-1 construction support the claim | Pass |
| `blp-trace-distance` | Eq. (1), \(|A|=\sqrt{A^\dagger A}\), range, and distinguishability discussion are correctly located on page 1 | **Repair atomicity:** the Claim bundles the formula, metric range, and operational interpretation; split the definition/range from the distinguishability fact or narrow the Claim |
| `blp-cpt-contraction` | Eq. (2), page 1, is copied correctly and properly restricted to CPT maps | Pass |
| `blp-divisible-monotonicity` | Eqs. (5) and (9), page 2, support nonincrease for a fixed pair under the source's CPT-divisible construction | Pass; retain the source-specific scope rather than upgrading it to every modern Markovianity notion |
| `blp-positive-rate-witness` | Eq. (10) and the next paragraphs on page 2 support the derivative, existential witness, and information-backflow interpretation | Pass |
| `blp-integrated-measure` | Eqs. (11)–(12), pages 2–3, support positive-interval integration/summation and maximization over all input pairs | Pass |
| `blp-finite-spin-bath` | Eq. (14) and page-4 discussion support periodic trace-distance exchange; nontrivial oscillation requires a pair with a nonzero coherence difference | Pass with that parameter qualification retained |
| `blp-optimization-limit` | page-4 conclusions support complete reduced dynamics for exact evaluation and observed growth as a lower bound | **Repair atomicity:** exact-evaluation requirements and the fixed-pair witness/lower-bound limitation are two independently reusable facts and should be split |
| `blp-gap-tensor-network` | complete-text inspection confirms the listed tensor-network/runtime notions are not established | **Repair atomicity:** PEPS bond, truncation error, state fidelity, timing, and monotonic entanglement growth are five distinct source-local absences; split them by assigned row or narrow this gap to one claim |

All BLP `Fact ID` relation endpoints resolve. The `blp-information-backflow` relation is not
internally normalized: its object ID denotes information backflow while its object label denotes
the positive trace-distance rate. Either make the object consistently the positive rate, or add
“information backflow” to the atomic Claim and use that as the object label. The other two relation
labels occur in their target Claims and are source concepts.

## BLP audit and operation replay

The assigned-row locators for Eq. (1), Eqs. (2)/(5)/(9), Eqs. (10)–(12), Eq. (14), and the
conclusion are correct. The source supports the distinction between a positive witness/lower bound
and the fully optimized measure.

Operation-replay rows 1, 2, and 4 are source-complete. Row 3 is not a transformation printed in BLP:
the paper defines continuous positive intervals, while “sum only positive successive increments”
is a discrete project derivation. The row must identify that transformation as an audit derivation,
not give BLP Eqs. (10)–(12) as though they were its exact discrete source location. With that
provenance repaired, the discrete positive-increment witness is consistent with the source.

No source-only judgment is made here on the benchmark application, dense route, numerical guard, or
candidate carrier described in the audit.

## McCloskey–Paternostro note: fact-by-fact review

| Fact ID | source / locator check | atomicity and semantic result |
|---|---|---|
| `mp-source-identity` | arXiv ID, v3 stamp, title, authors, and 7-page count are correct | **Repair:** the PRA publication assertion and “journal reference” locator do not resolve in the fixed PDF; add page 1 to `visually_checked_pages` and preserve both visible date lines |
| `mp-selection-scope` | abstract and opening discussion on pages 1–2 support the claim | Pass |
| `mp-system-collision` | Eqs. (1)–(2), page 2, support the partial-SWAP unitary and displayed SWAP matrix | Pass |
| `mp-environment-collision` | Eqs. (3)–(4), page 2, support the adjacent-ancilla partial SWAP with \(\delta\) | Pass |
| `mp-joint-reduced-evolution` | Eq. (5) and following paragraph, page 2, support overall unitary evolution and environment discard for reduced dynamics | Pass |
| `mp-trace-distance` | Eqs. (6)–(7), page 3, support trace distance and the positive-time derivative measure | Pass |
| `mp-gap-equation-eight` | visual inspection confirms the self-distance defect | **Repair completeness and gap shape:** record the missing positive-increment restriction as a separate atomic defect; phrase the gap as the absence of a literally usable discrete formula, with the observed print defects as support |
| `mp-strategy-one` | Eq. (10) and surrounding page-4 prose support early erasure of system–ancilla correlations | Pass |
| `mp-strategy-two` | Eq. (11) and surrounding page-4 prose support retaining the correlation through the ancilla's remaining active role | Pass |
| `mp-retention-finding` | Figs. 3–4 and pages 4–5 support stronger revivals/non-Markovianity and a lower threshold in \(\delta\) for Strategy 2 | **Repair correctness and atomicity:** “earlier trace-distance revivals” is not the source's stated result; replace it with the lower interaction-strength threshold. Split the additional claims that both strategies can be non-Markovian and that behavior depends on strength/preparation. Add page 5 to `visually_checked_pages` because this fact relies on Fig. 4 |
| `mp-stochastic-collisions` | page 6 supports “draw a random variable; collide if it is below a threshold in \([0,1]\)” and, for \(\delta=\pi/2\), changed period with unchanged amplitude | **Repair atomicity and scope:** split the event rule from the full-swap period/amplitude finding. The PDF does not specify the random variable's distribution, so it does not by itself establish that the threshold numerically equals a Bernoulli collision probability |
| `mp-gap-monotonic-entanglement` | complete-text inspection confirms that monotonic tensor-network/resource growth is not established | **Repair atomicity:** entanglement, bond dimension, truncation error, and runtime are four distinct source-local absences; split them by assigned row or narrow the Claim |

All three McCloskey–Paternostro relation endpoints resolve, and their object labels name concepts in
the corresponding Claims. Their predicates are semantically compatible with the source records.

## McCloskey–Paternostro audit and operation replay

The coherent-collision assigned row introduces a generic \(\alpha\) that the source does not use.
The source uses \(\gamma\) for \(S\)-\(E_j\) and \(\delta\) for \(E_j\)-\(E_{j+1}\). The row must keep
those two symbols rather than merge them into an undefined source symbol.

The retained-versus-erased rows and their Eqs. (10)–(11) locators are correct. The discrete-backflow
row correctly refuses literal Eq. (8), but must record both printed defects described above. The
monotonic tensor-network conclusion remains source-local only.

Operation-replay rows 1–3 are complete against Eqs. (1)–(5) and (10)–(11). Row 4 is acceptable only
as an explicitly cross-source audit derivation: the repaired positive-increment expression comes
from discretizing BLP, not from literal McCloskey Eq. (8). Row 5 is incomplete because “one declared
Bernoulli rule” silently supplies a distribution not given in the PDF. It must instead:

- replay only the source-stated draw-and-threshold rule; or
- declare a uniform draw/Bernoulli mask as a separate project choice and mark the source-local
  distribution bridge missing.

The audit's assigned-row verdict “closed for a Bernoulli event knob” therefore overstates source
closure and must be changed.

The partial-SWAP Pauli decomposition is currently in `Project application`, not in the replay table.
If it is load-bearing for an application, add a project-derivation replay row with the exact
\(e^{+i\gamma/2}\) phase relation and the consuming gate API's sign convention. The algebra itself
is correct and does not need substantive reversal.

No source-only judgment is made here on the proposed ladder, candidate carriers, timing, truncation,
or corruption tests.

## Required repair checklist

1. Remove or separately source the two journal-publication assertions; replace the non-resolving
   “journal reference” locators and record the two visible date lines in each fixed artifact.
2. Split or narrow the non-atomic BLP records `blp-trace-distance`,
   `blp-optimization-limit`, and `blp-gap-tensor-network`.
3. Normalize the BLP information-backflow relation's object ID and label.
4. Mark the BLP positive-successive-increment replay as a discrete audit derivation rather than an
   equation printed in BLP.
5. Split McCloskey Eq. (8)'s self-distance error and missing-positive-selector error into atomic
   source-local defects; do not describe the repaired formula as McCloskey's printed equation.
6. Replace the unsupported “earlier trace-distance revivals” with the source-supported lower
   \(\delta\)-threshold result, split the extra retention findings, and add PDF page 5 to the visual
   ledger.
7. Split `mp-stochastic-collisions`; record that the random-variable distribution is unspecified,
   and downgrade the audit's Bernoulli-closure verdict to a project choice/source-local missing
   bridge.
8. Split or narrow `mp-gap-monotonic-entanglement`.
9. Replace the audit's undefined generic \(\alpha\) with the source's distinct \(\gamma\) and
   \(\delta\).
10. Add the partial-SWAP-to-Pauli application replay with the exact global phase and consuming
    rotation-sign convention if that bridge is retained as load-bearing.
11. Recompute each changed audit SHA-256 in its note and repeat independent source-only review
    before changing either pending admission status.

## Source-local completion status

| assigned row | exact source location | paper says | paper does not say | status |
|---|---|---|---|---|
| BLP trace-distance witness and optimized measure | BLP Eqs. (1), (10)–(12), PDF pp. 1–3 | positive trace-distance growth for a pair is a witness/lower bound; optimization over all pairs gives \(\mathcal N\) | it does not print the audit's discrete sampled formula | closed at continuous-source scope; discrete bridge requires provenance repair |
| BLP finite-spin recurrence | BLP Eq. (14) and discussion, PDF p. 4 | suitable initial pairs show periodic information exchange and divergent accumulated measure | it does not establish tensor-network/resource monotonicity | closed at source scope |
| McCloskey collision primitive | McCloskey Eqs. (1)–(5), PDF p. 2 | coherent system–ancilla and ancilla–ancilla partial SWAPs compose the collision model | it does not print the Pauli-product decomposition | closed; Pauli decomposition is a correct separate derivation |
| McCloskey correlation strategies | McCloskey Eqs. (10)–(11), Figs. 3–4, PDF pp. 4–5 | correlation retention materially changes the revival strength and lowers the \(\delta\) threshold | it does not state “earlier revivals” as the comparison result | claim requires repair |
| McCloskey discrete measure | McCloskey Eqs. (7)–(8), PDF p. 3 | Eq. (7) defines positive trace-distance growth | printed Eq. (8) supplies neither a valid previous-pair distance nor an explicit positive selector | contradicted as printed; candidate gap incomplete |
| McCloskey stochastic collision rule | McCloskey Sec. II.B and Fig. 6, PDF p. 6 | a random draw is compared with a threshold; the displayed full-swap case changes period, not amplitude | it does not specify the draw distribution needed to identify threshold with Bernoulli probability | missing for the audit's Bernoulli closure |

- independent `read_status`: complete for both fixed PDFs
- candidate `evidence_status`: persisted but not independently admissible
- admission verdict: **REQUIRED REPAIRS**

