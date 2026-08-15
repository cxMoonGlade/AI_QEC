+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1302.3865"
source_version = "v4"
source_uri = "https://arxiv.org/abs/1302.3865v4"
source_artifact = "docs/papers/1302.3865v4.pdf"
source_sha256 = "f6068e2f2bf441b09b4da071ca51a680fb2bf0c895cac68f853a439c64b600fe"
title = "Upper bounds on mixing rates"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/ENTANGLEMENT_RATE_ACCUMULATION_AUDIT_2026-07-31.md"
audit_packet_sha256 = "4074a046a04caa1983439a912566aab04e484ceda4d374ecf0104b5b6a824e44"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_entangling_rate_source_review_2026_07_31"
admission_date = "2026-07-31"
visually_checked_pages = [1, 2, 3, 4]

[[relations]]
predicate = "defines"
object_id = "lv-mixing-rate"
object_type = "observable"
object_label = "mixing rate"
fact_id = "lv-mixing-rate-definition"

[[relations]]
predicate = "defines"
object_id = "sim-conjecture-binary-entropy"
object_type = "concept"
object_label = "binary entropy"
fact_id = "lv-sim-conjecture"

[[relations]]
predicate = "derives"
object_id = "lv-square-root-bound"
object_type = "theorem"
object_label = "bounded above"
fact_id = "lv-binary-theorem"

[[relations]]
predicate = "limits"
object_id = "lv-loose-at-small-p"
object_type = "limitation"
object_label = "significantly worse"
fact_id = "lv-small-p-looseness"

[[relations]]
predicate = "limits"
object_id = "sim-binary-entropy-open"
object_type = "limitation"
object_label = "still open"
fact_id = "lv-open-question"

[[relations]]
predicate = "defines"
object_id = "lv-small-total-mixing"
object_type = "theorem"
object_label = "average entropy"
fact_id = "lv-small-total-mixing"

[[relations]]
predicate = "supports"
object_id = "sim-implies-sie"
object_type = "concept"
object_label = "generalization"
fact_id = "lv-sim-sie-relation"

[[relations]]
predicate = "defines"
object_id = "lv-small-total-entangling"
object_type = "theorem"
object_label = "total change"
fact_id = "lv-small-total-entangling"
+++
# Full-text review — Lieb and Vershynina, “Upper bounds on mixing rates”

## Source identity [paper_fact]
Fact ID: lv-source-identity
Source locator: Title page, author block, and arXiv stamp
PDF page: 1
Claim: The reviewed source is arXiv:1302.3865v4 by Elliott H. Lieb and Anna Vershynina, both at Princeton, nine pages, with the version stamp dated 5 Nov 2013.

The internal date line reads July 25, 2018, which is later than the arXiv version stamp;
the version pinned here is v4. The artifact has nine pages, and every claim recorded below
is on pages 1–4.

## Mixing rate definition [paper_fact]
Fact ID: lv-mixing-rate-definition
Source locator: Sec. 2, definition following the displayed \(\rho(t)\), PDF p. 3
PDF page: 3
Claim: For a binary ensemble \(\mathcal E_2=\{(p,\rho_1),(1-p,\rho_2)\}\) with \(\rho(t)=p\rho_1+(1-p)e^{-iHt}\rho_2 e^{iHt}\), the **mixing rate** is \(\Lambda(\mathcal E_2,H)=\frac{dS(\rho(t))}{dt}\big|_{t=0}\).

The Hamiltonian acts on \(\rho_2\) but not on \(\rho_1\). Equation (2.1) gives the useful
forms \(\Lambda=-ip\mathrm{Tr}([\rho_1,\ln\rho]H)=i(1-p)\mathrm{Tr}([\rho_2,\ln\rho]H)\),
and the maximum over \(\|H\|=1\) is \(\Lambda(\mathcal E_2)=p\|[\rho_1,\ln\rho]\|_1\),
attained at \(H=1-2R\) with \(R\) the projector on the negative eigenspace of
\(i[\rho_1,\ln\rho]\).

## The conjecture [paper_fact]
Fact ID: lv-sim-conjecture
Source locator: Sec. 2.1 CONJECTURE (Bravyi), Small Incremental Mixing
PDF page: 3
Claim: Bravyi's Small Incremental Mixing conjecture states that the maximum mixing rate is bounded above by a **binary entropy**, \(\Lambda(\mathcal E_2)\le S(p)=-p\ln p-(1-p)\ln(1-p)\).

The source records that Bravyi proved \(\Lambda(\mathcal E_2)\le6S(p)\) in the special case
where \(\rho\) has at most two distinct eigenvalues of arbitrary multiplicity, and that for
the general case he gave a dimension- and \(p\)-independent bound of 2.

## The theorem proved [paper_fact]
Fact ID: lv-binary-theorem
Source locator: Sec. 2.2 THEOREM (Binary case); abstract, PDF p. 1
PDF page: 4
Claim: For any binary ensemble the maximum mixing rate is **bounded above** by \(\Lambda(\mathcal E_2)\le4\sqrt{p(1-p)}\), for any Hamiltonian of norm one, and the constant is independent of the dimension of the Hilbert space including the infinite-dimensional case.

The proof is given in Chapter 3 as the special case of Theorem 3.2 for a general ensemble
of any number of states.

## Looseness at small probability [paper_fact]
Fact ID: lv-small-p-looseness
Source locator: Paragraph following the displayed bound, PDF p. 2
PDF page: 2
Claim: The proved bound "has a shape similar to that of the binary entropy … up to a factor of 2", but its \(\sqrt p\) behaviour near \(p=0\) is stated to be **significantly worse** than \(p\ln p\).

This is the source's own assessment of where its bound is weakest, and it is the regime of
small mixing probability.

## The binary-entropy question is open [paper_fact]
Fact ID: lv-open-question
Source locator: Paragraph beginning "The question of bounding a mixing rate", PDF p. 2
PDF page: 2
Claim: The source states that bounding a mixing rate by a binary entropy for an ensemble of two states is **still open**, and that the analogous conjecture bounding a general ensemble by a Shannon entropy is open as well.

For the special case Bravyi treated, the source says one would hope to improve the
constant 6 in front of the binary entropy.

## Small total mixing [paper_fact]
Fact ID: lv-small-total-mixing
Source locator: Sec. 2, "Small Total Mixing. (Binary case)", PDF p. 3
PDF page: 3
Claim: For any fixed binary ensemble the entropy at any time satisfies \(\overline S(\mathcal E_2)\le S(\rho(t))\le\overline S(\mathcal E_2)+S(p)\), where \(\overline S\) is the **average entropy** of the ensemble and \(S(p)\) the binary entropy.

The source states this follows from basic properties of the von Neumann entropy and proves
the general-ensemble version in Chapter 3.

## Relation to the entangling problem [paper_fact]
Fact ID: lv-sim-sie-relation
Source locator: Paragraph beginning "Bravyi introduced the Small Incremental Mixing problem", PDF p. 2
PDF page: 2
Claim: Small Incremental Mixing was introduced by Bravyi as a **generalization** of the Small Incremental Entangling conjecture, which was first proposed to him by Kitaev and bounds the rate of change of entanglement between two parties under non-local unitary evolution by \(c\ln d\).

The constant \(c\) is stated to be independent of either party's dimension.

## Small total entangling [paper_fact]
Fact ID: lv-small-total-entangling
Source locator: Sec. 2, "Small Total Entangling", PDF p. 4
PDF page: 4
Claim: The **total change** of the entanglement \(E(\rho(t))\) is at most \(2\ln d\), where \(d=\min(\dim A,\dim B)\).

The setting is Alice and Bob controlling \(A,a\) and \(B,b\) respectively, starting from a
pure state on \(aABb\) and evolving under \(U(t)=I_a\otimes e^{iH_{AB}t}\otimes I_b\), with
entanglement entropy \(E(\rho(t))=S(\rho_{aA}(t))\). The source attributes the proof to
its reference [8].
