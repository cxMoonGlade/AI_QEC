+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1304.5931"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1304.5931v2"
source_artifact = "docs/papers/1304.5931v2.pdf"
source_sha256 = "5114c36fb30c73fb89bd26e3fafab563360c9124407378109b0ab320a9c5e55b"
title = "Entanglement rates and area laws"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/ENTANGLEMENT_RATE_ACCUMULATION_AUDIT_2026-07-31.md"
audit_packet_sha256 = "4074a046a04caa1983439a912566aab04e484ceda4d374ecf0104b5b6a824e44"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_entangling_rate_source_review_2026_07_31"
admission_date = "2026-07-31"
visually_checked_pages = [1, 2, 3, 4, 5]

[[relations]]
predicate = "defines"
object_id = "vanacoleyen-entangling-rate"
object_type = "observable"
object_label = "entanglement rate"
fact_id = "va-rate-definition"

[[relations]]
predicate = "defines"
object_id = "sie-conjecture"
object_type = "concept"
object_label = "small incremental entangling"
fact_id = "va-sie-statement"

[[relations]]
predicate = "supports"
object_id = "sie-proved-constant-18"
object_type = "theorem"
object_label = "conjectured bound"
fact_id = "va-sie-proved"

[[relations]]
predicate = "derives"
object_id = "va-lambda-p-log-bound"
object_type = "theorem"
object_label = "improvement"
fact_id = "va-lambda-bound"

[[relations]]
predicate = "uses"
object_id = "dur-ancilla-free-constant"
object_type = "model"
object_label = "absence of ancillas"
fact_id = "va-ancilla-free-constant"

[[relations]]
predicate = "derives"
object_id = "va-variational-recasting"
object_type = "method"
object_label = "variational problem"
fact_id = "va-recasting"

[[relations]]
predicate = "supports"
object_id = "va-area-law-quasi-adiabatic"
object_type = "theorem"
object_label = "area law"
fact_id = "va-area-law"

[[relations]]
predicate = "limits"
object_id = "va-single-interaction-scope"
object_type = "limitation"
object_label = "reference time"
fact_id = "va-scope"
+++
# Full-text review — Van Acoleyen, Mariën, and Verstraete, “Entanglement rates and area laws”

## Source identity [paper_fact]
Fact ID: va-source-identity
Source locator: Title page, author block, and arXiv stamp
PDF page: 1
Claim: The reviewed source is arXiv:1304.5931v2 by Karel Van Acoleyen, Michael Mariën, and Frank Verstraete, five pages, later published as Physical Review Letters 111, 170501.

The arXiv stamp reads 13 May 2013. Affiliations are Ghent University and the Vienna
Center for Quantum Science and Technology. The artifact has five pages, the last of which
is the reference list.

## Entangling rate definition and scope [paper_fact]
Fact ID: va-rate-definition
Source locator: Eq. (1) and the paragraph introducing it
PDF page: 1
Claim: The **entanglement rate** is \(\Gamma=\frac{dS_{aA}(t)}{dt}\big|_{t=0}\) for a pure state on \(aABb\) evolving under \(U(t)=e^{iH_at}\otimes e^{iH_{AB}t}\otimes e^{iH_bt}\), where \(a\) and \(b\) are ancillas that do not directly interact.

The source states that although \(H_a\) and \(H_b\) do not contribute to the rate directly,
the ancillas can influence it indirectly through their entanglement with the rest, and
that this indirect influence is what the paper addresses.

## Bound at one reference time [paper_fact]
Fact ID: va-scope
Source locator: Final sentence of the paragraph following Eq. (1)
PDF page: 1
Claim: The bound is on the entanglement rate at some particular arbitrary **reference time**, as opposed to a bound on the average rate over a period.

The source makes this distinction explicitly, so the result constrains an instantaneous
rate rather than a time-averaged quantity.

## Ancilla-free constant [paper_fact]
Fact ID: va-ancilla-free-constant
Source locator: First paragraph of the left column, sentence beginning "It was shown that"
PDF page: 2
Claim: In the **absence of ancillas** the maximal rate satisfies \(\Gamma_{\max}\equiv\max_\Psi\Gamma\le\beta\|H\|\) with \(\|H\|\) the operator norm of the interacting Hamiltonian and \(\beta\simeq1.9123\).

The source attributes this to its reference [1] and records that the same authors observed
that ancillas can generically increase the maximal entanglement rate. It also records
Bravyi's general no-ancilla solution \(\Gamma_{\max}\le c(d)\|H\|\log d\) with
\(c(2)=\beta\) and \(c(d)\to1\) for large \(d\).

## The conjecture [paper_fact]
Fact ID: va-sie-statement
Source locator: Eq. (2) and the sentence introducing it
PDF page: 2
Claim: The **small incremental entangling** conjecture, attributed to Kitaev and put forward by Bravyi, is \(\Gamma_{\max}\le c\|H\|\log d\) with \(d=\min(d_A,d_B)\) and \(c\) an order-one constant independent of \(d\), for ancilla-assisted entanglement rates.

The source notes that prior results implied only the weaker \(\Gamma_{\max}\le c\|H\|d^4\)
and \(\Gamma_{\max}\le2\|H\|d^2\), improved by Lieb and Vershynina to
\(\Gamma_{\max}\le(4/\ln2)\|H\|d\), which for large systems remains exponentially weaker
than the conjecture.

## The conjecture proved [paper_fact]
Fact ID: va-sie-proved
Source locator: Sentence "We will obtain c = 18" on PDF p. 2; conclusion, first paragraph
PDF page: 2
Claim: The source proves the **conjectured bound** with the explicit constant \(c=18\), and its conclusion states the resulting bound is optimal to within a constant with logarithmic scaling in the dimension of the subsystem the Hamiltonian acts on nontrivially.

The conclusion on PDF p. 5 identifies the result as the bound "originally conjectured by
Bravyi and Kitaev". The source adds that the prefactor is "probably not optimal" and that
Bravyi's own numerical examples suggested \(c''=1\), which for large \(d\) would give
\(\Gamma_{\max}\lesssim2\|H\|\log d\).

## Variational recasting [paper_fact]
Fact ID: va-recasting
Source locator: Eqs. (3), (4), (5), (6)
PDF page: 2
Claim: The rate is written \(\Gamma=-i\,\mathrm{Tr}(H_{AB}[\rho_{aA},\log\rho_A\otimes I_B])\) and recast as \(\Gamma=\frac1p\Lambda(p)\), turning the optimisation over \(H\) into a **variational problem** over projectors, \(\max_{\|H\|=1}|\Lambda(p)|=2\max_P|\mathrm{Tr}(P[X,\log Y])|\).

The identification is \(X=\rho_{aA}/d_B^2\), \(Y=\rho_A\otimes I_B/d_B\), \(p=1/d_B^2\le1/2\),
subject to \(\|H\|=1\), \(\mathrm{Tr}X=p\), \(\mathrm{Tr}Y=1\), \(0\le X\le Y\).

## The central inequality [paper_fact]
Fact ID: va-lambda-bound
Source locator: Eq. (15) and the sentence following it
PDF page: 3
Claim: The proof yields \(\Lambda(p)\le9p\log(1/p)\) for \(p<1/e^2\), stated as an **improvement** on the earlier \(\Lambda(p)\le\frac{4}{\ln2}\sqrt{p(1-p)}\) for \(p<0.0085\).

The derivation groups the eigenvalues of \(Y\) into geometric intervals (Eq. 8), rearranges
the sum (Eq. 9), applies the Kittaneh commutator inequality (Eq. 10) and Cauchy–Schwarz
(Eq. 14). Substituting Eq. (15) into Eq. (4) gives the rate bound with \(c=18\).

## Area-law application [paper_fact]
Fact ID: va-area-law
Source locator: Eqs. (17)–(21) and the concluding paragraph of Sec. "Area law for quasi-adiabatic continuation"
PDF page: 4
Claim: Combining the rate bound with quasi-adiabatic continuation gives \(\frac{dS_L(s)}{ds}\lesssim A\frac{\|h'(s)\|}{\gamma(s)}\xi(s)^{D+2}\log d_l\), an **area law** for the variation of the subsystem entanglement entropy along an adiabatic path.

Integrating gives \(\Delta S_L\le A\tilde c(s)\log d_l\) with \(\tilde c\) independent of
system size and boundary area, so an entropy area law for one gapped system implies an
area law for all systems in the same quantum phase, in any dimension and on any lattice.
The source states this holds for topological phases as well.
