# Source-only claim audit — Hostens, Dehaene, and De Moor, arXiv:quant-ph/0408190v2

Date: 2026-07-27

Packet status: `source_only_reviewed`

Source artifact: `docs/papers/quant-ph_0408190v2.pdf`

Pinned source URI: `https://arxiv.org/abs/quant-ph/0408190v2`

Source SHA-256:
`b48cf81d89050ccf9372d5be713c098088fd3a0d371e9be2a9901d09ef07c831`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `PASS`

Independent review packet:
`docs/simulator_validation/HOSTENS_QUANT_PH_0408190V2_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`

Independent review packet SHA-256:
`e98dd6aa8df1259da77ffd94c77fb8d70a8e041d1f6043fc3ebfa6991491224b`

The complete 11-page PDF was read in source order. Every page was also rendered
and visually inspected. The load-bearing definitions, equations, theorem, and
printed anomalies were checked on rendered PDF pp. 1--11; text extraction was
used for navigation, not as a substitute for those checks.

The local artifact is a valid, unencrypted PDF 1.4 with 11 pages and a terminal
EOF marker. Its visible footer identifies `arXiv:quant-ph/0408190v2 22 Feb
2005`. The title page instead prints `(Dated: October 23, 2018)`, and the PDF
metadata has a 2018 creation/modification date. This packet therefore treats
the reviewed object as the pinned version-2 arXiv preprint and preserves the
date discrepancy as an artifact anomaly rather than silently choosing one
date.

This packet separates source statements from project application. In
particular, arbitrary-\(d\) Pauli and stabilizer algebra includes the special case
`d = 3`, but that inclusion is not evidence for a computational-versus-leakage
sector, a leakage channel, or a qutrit-specific Clifford quotient.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| arbitrary-dimensional Pauli algebra | PDF p. 2, Sec. II.A, Eqs. (1)--(6) | A qudit has computational labels in \(\mathbb Z_d\); generalized Paulis are represented by \(a=[v;w]\in\mathbb Z_d^{2n}\), with a \(\zeta^\delta\) phase and multiplication/commutation controlled by \(U\) and \(P=U-U^T\). | It does not split the local Hilbert space into computational and leakage sectors. | `closed` |
| even- versus odd-\(d\) phases | PDF p. 2, paragraph after Eq. (6); PDF pp. 9--10, Appendix C, Eqs. (C1)--(C8) | For even \(d\), some \(XZ(a)\) have order \(2d\), motivating \(\zeta^\delta\); for odd \(d\), \(2\) is invertible and an \(\omega\)-phase representation with vectors over \(\mathbb Z_d\) is available. | The odd-\(d\) simplification does not turn \(\mathbb Z_d\) into a field when \(d\) is composite. | `closed` |
| Clifford representation and update | PDF pp. 2--3, Secs. II.B--II.C, Eqs. (7)--(10) | A Clifford normalizes the Pauli group and is represented up to global phase by \(C\in\mathbb Z_d^{2n\times2n}\) and \(h\in\mathbb Z_{2d}^{2n}\); Eq. (7) gives conjugation, Eqs. (8)--(9) composition/inversion, and symplecticity plus Eq. (10) constrain \((C,h)\). | A symplectic label update alone omits the source's phase data in the general even-\(d\) setting. | `closed` |
| sufficiency and elementary realization | PDF pp. 3--6, Secs. III--IV | The source supplies Pauli, embedded local, invertible configuration-space, permutation, SUM, Fourier, and phase operations, and uses them to construct every valid \((C,h)\) from at-most-two-qudit operations. | It does not give a hardware-native compilation cost or noise-aware implementation. | `closed` at algebraic decomposition scope |
| composite-\(d\) row reduction | PDF pp. 4--6, Sec. IV | Scaling by \(r\in\mathbb Z_d\) is permitted only when \(\gcd(r,d)=1\); a symplectic column need not contain an individually invertible entry, so Euclid's algorithm combines entries until their gcd is a unit. | Field-style Gaussian elimination is not justified for arbitrary composite \(d\). | `closed` |
| stabilizer definition | PDF p. 6, Sec. V.A, opening paragraphs and Eq. (11) | A stabilizer state is the common \(+1\) eigenstate of a subgroup of \(d^n\) commuting Pauli elements containing no nonidentity scalar multiple of identity; \(S\) and \(f\) encode generators, with \(S^TPS=0\) and Eq. (11) enforcing the scalar-identity exclusion. | The source does not define a noisy stabilizer-code experiment or syndrome instrument. | `closed` |
| composite-\(d\) generator count | PDF p. 6, Sec. V.A, paragraph before Eq. (11) | The source permits \(m>n\), prints “If \(d\) has only single prime factors, then \(m=n\)” and “If \(d\) has multiple prime factors, \(n\le m\le2n\),” and gives a \(d=4,n=1\) state with two generators. | The paper does not use modern square-free/repeated-prime terminology, so this packet does not silently substitute it for the printed wording. | `closed` for exact source wording; terminology flagged |
| stabilizer updates | PDF p. 6, Sec. V.A, Eqs. (12)--(15) | Eq. (12) updates generators under an invertible column transformation; Eq. (13) updates a stabilizer under a Clifford; Smith normal form yields a minimal generator matrix and Eqs. (14)--(15) express minimality and phase conditions. | These are unitary/generator-coordinate updates, not measurement-conditioned stabilizer updates. | `closed` |
| standard-basis expansion | PDF pp. 7--8, Theorem 1, Eqs. (16)--(19); PDF pp. 8--9, Appendices A--B | Smith-normal reduction gives the canonical form in Eq. (16); Eqs. (17)--(18) give a direct quadratic-phase standard-basis expansion and a uniquely defined offset, with Appendix B proving uniqueness. | This theorem does not define Born branches, reset, or emitted classical records. | `closed` |
| graph-state scope | PDF pp. 1 and 6, Introduction and Sec. V.A | The source says that for non-field configuration spaces not all stabilizer states are graph-state equivalent without an extra condition and therefore uses matrices with possibly more than \(n\) columns. | It does not prove unrestricted graph-state equivalence at composite \(d\). | `closed` |
| measurements and trajectories | documented full-text scope, represented by PDF p. 8, Conclusion | The source develops Pauli/Clifford algebra and pure stabilizer-state expansions. | It gives no stabilizer measurement update, projective instrument, Born probability, conditional state, reset map, raw history, or emitted Record. | `missing` |
| leakage and return | documented full-text scope, represented by PDF p. 8, Conclusion | The source models a complete \(d\)-level computational space. | It gives no computational/leakage sector split, leakage/seepage channel, leakage flag, or return dynamics. | `missing` |
| tensor-network bridge | documented full-text scope, represented by PDF p. 8, Conclusion | The source gives a direct basis expansion of stabilizer states. | It gives no MPS, PEPS, Clifford-augmented PEPS, CAPEPS update, contraction algorithm, or tensor-network benchmark. | `missing` |
| QEC resources | PDF p. 1, Introduction, motivation paragraph; PDF p. 8, Conclusion | The authors explicitly say their motivation is not the study of stabilizer codes and their error-correcting capacities. | It gives no threshold, decoder, syndrome-circuit, detector model, matched resource benchmark, or circuit-noise result. | `missing` |
| qutrit local-equivalence enumeration | documented full-text scope, represented by PDF p. 3, Sec. III opening | The arbitrary-\(d\) formalism includes \(d=3\) as one specialization. | It gives no qutrit-specific 90-class entanglement quotient, no one- or double-sided local-equivalence enumeration, and no executable list of such representatives. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(d\) | one-qudit Hilbert-space dimension and modulus | nonzero integer dimension; labels in \(\mathbb Z_d\) | fixed for a system | PDF pp. 1--2, Introduction and Sec. II.A |
| \(\omega\) | primitive \(d\)-th root of unity | complex phase | fixed | PDF p. 2, Eq. (1) |
| \(\zeta\) | a square root of \(\omega\) | complex phase; exponent in \(\mathbb Z_{2d}\) | fixed choice | PDF p. 2, paragraph before Eq. (4) |
| \(X,Z\) | cyclic shift and phase operators | one-qudit unitaries | fixed generators | PDF p. 2, Eq. (1) |
| \(a=[v;w]\) | exponent vector for \(XZ(a)=X^vZ^w\) | \(\mathbb Z_d^{2n}\) | variable | PDF p. 2, Eqs. (2)--(3) |
| \(U\) | block matrix controlling the multiplication phase | \(\begin{bmatrix}0&0\\I&0\end{bmatrix}\) | fixed | PDF p. 2, Eq. (4) and following definition |
| \(P\) | alternating commutation form | \(U-U^T\pmod d\) | fixed | PDF p. 2, Eqs. (5)--(6) |
| \(C\) | Pauli-label action of a Clifford | \(\mathbb Z_d^{2n\times2n}\), symplectic | operation-dependent | PDF pp. 2--3, Eq. (7) and Sec. II.C |
| \(h\) | phase images of the \(2n\) standard Pauli generators | \(\mathbb Z_{2d}^{2n}\), subject to Eq. (10) | operation-dependent | PDF pp. 2--3, Eqs. (7) and (10) |
| \(g\) | odd-\(d\) phase vector \(h/2\) | \(\mathbb Z_d^{2n}\) | operation-dependent | PDF p. 9, Appendix C, Eqs. (C2)--(C4) |
| \(S\) | stabilizer generator matrix, with generator labels as columns | \(\mathbb Z_d^{2n\times m}\) | state/generator-choice dependent | PDF p. 6, Sec. V.A |
| \(f\) | stabilizer generator phase vector | \(\mathbb Z_{2d}^{m}\) | generator-choice dependent | PDF p. 6, Sec. V.A and Eq. (11) |
| \(R\) | invertible stabilizer generator-coordinate change | \(\mathbb Z_d^{m\times m}\) | variable | PDF p. 6, Eq. (12) |
| \(Q,B,T\) | Smith-normal canonical blocks and configuration-space transform in Theorem 1 | matrices over \(\mathbb Z_d\) | state-dependent | PDF p. 7, Eq. (16) |
| \(M,p,x^*\) | quadratic form, linear phase, and affine offset in the basis expansion | modular matrix/vector data | state-dependent | PDF p. 7, Eqs. (17)--(18) |
| \(q_k\) | moduli derived from the diagonal of the Smith-normal block \(Q\) | divisor of \(d\), with zero diagonal mapped to \(d\) | state-dependent | PDF p. 7, definitions below Eq. (17) |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| \(\zeta^\delta XZ(a)\), \(\zeta^\epsilon XZ(b)\) | multiply exponent labels modulo \(d\) and phases modulo \(2d\) | \(a,b\in\mathbb Z_d^{2n}\) and the fixed block matrix \(U\) | Eq. (4), with label \(a+b\) and phase \(\delta+\epsilon+2a^TUb\) | PDF p. 2, Eq. (4) | `closed` |
| two generalized Paulis | compare the two multiplication orders | \(P=U-U^T\) | commutation phase \(\omega^{a^TPb}\) | PDF p. 2, Eqs. (5)--(6) | `closed` |
| Clifford data \((C,h)\) and Pauli data \((a,\delta)\) | repeatedly apply Eq. (4) to the images of the standard generators | phase arithmetic remains modulo \(2d\), even though \(C\) is over \(\mathbb Z_d\) | label \(b=Ca\pmod d\) and the printed phase polynomial \(\epsilon\pmod{2d}\) | PDF pp. 2--3, Eq. (7) | `closed` |
| Clifford data \((C,h)\), \((C',h')\) | compose the represented conjugations | each pair satisfies the Clifford conditions | Eq. (8) for \((C'',h'')\) | PDF p. 3, Eq. (8) | `closed` |
| Clifford data \((C,h)\) | invert the conjugation | symplectic \(C\), so \(C^{-1}=-PC^TP\pmod d\) | Eq. (9) for \((C^{-1},h')\) | PDF p. 3, Eq. (9) and paragraph below | `closed` |
| symplectic \(C\) and admissible \(h\) | reduce \(C\) to identity by embedded elementary row operations, reverse the operations, then correct \(h\) with a Pauli | row scalings use only units; Euclid's algorithm handles columns with no unit entry | realization by one- and two-qudit Clifford operations | PDF pp. 4--6, Sec. IV | `closed` constructively |
| stabilizer data \((S,f)\) and generator transform \(R\) | replace the generator columns by \(SR\) and propagate multiplication phases | \(R\) invertible over \(\mathbb Z_d\) | Eq. (12) | PDF p. 6, Eq. (12) | `closed` |
| stabilizer data \((S,f)\) and Clifford data \((C,h)\) | conjugate every stabilizer generator using Eq. (7) | unitary Clifford operation | Eq. (13), including \(S'=CS\) and phase update | PDF p. 6, Eq. (13) | `closed` for unitary conjugation only |
| arbitrary stabilizer state | apply a configuration-space Clifford and a Smith-normal generator change | \((S,f)\) satisfies commutation and phase conditions | canonical stabilizer form in Eq. (16) | PDF p. 7, Theorem 1(i) | `closed` |
| canonical data \((Q,B,f')\) | solve \(B^Tx=y\pmod q\), then sum the corresponding basis kets with quadratic phases | Appendix B's stabilizer-derived solvability and uniqueness conditions | direct basis expansion Eqs. (17)--(18), unique \(x^*\in G_{\bar q}\) | PDF pp. 7--9, Theorem 1(ii) and Appendix B | `closed` |
| odd \(d\) | divide the even phase vectors by two in \(\mathbb Z_d\) and replace \(\zeta\)-powers by \(\omega\)-powers | \(2^{-1}=(d+1)/2\) exists modulo \(d\) | simplified Pauli, Clifford, stabilizer, and expansion formulas (C1)--(C8) | PDF pp. 9--10, Appendix C | `closed`; derivations are stated to be omitted |

## Composite-d subtleties

1. The arithmetic is over the ring \(\mathbb Z_d\), which is not generally a
   field. A nonzero element is not necessarily invertible. Sec. IV explicitly
   tests \(\gcd(r,d)=1\) before using a row scale.
2. Symplectic invertibility constrains an entire column but does not guarantee
   that the column contains an individually invertible entry. The source uses
   repeated gcd formation via Euclid's algorithm to create a unit.
3. The source permits a minimal stabilizer generator count above \(n\) and
   gives the concrete \(d=4,n=1\) example
   \((\lvert0\rangle+\lvert2\rangle)/\sqrt2\), stabilized by
   \(\{I,X^2,Z^2,X^2Z^2\}\), with \(m=2\).
4. The Introduction says that when the one-qudit configuration space is not a
   field, not every stabilizer state is graph-state equivalent without an
   extra condition. The paper's more general \(S\) may therefore have more
   than \(n\) columns.
5. Appendix A uses Smith normal form over the principal ideal ring
   \(\mathbb Z_d\); field-only row-reduction assumptions must not be imported.
6. Odd \(d\) only makes division by two available. Composite odd \(d\) can
   still have zero divisors and nonunits.

## Printed and artifact anomalies

| anomaly | exact locator | source-local handling |
|---|---|---|
| visible date mismatch | PDF p. 1, title block versus arXiv footer | Preserve both `(Dated: October 23, 2018)` and `arXiv:quant-ph/0408190v2 22 Feb 2005`; identify the evidence object by the pinned arXiv version. |
| “one and two-qubit” inside arbitrary-qudit discussion | PDF p. 2, final paragraph of the Introduction; PDF p. 3, Sec. III opening | Treat as printed terminology. Sec. IV and the Conclusion say one- and two-qudit, and the displayed operations are arbitrary-\(d\), but the wording is not silently corrected in quoted scope. |
| decomposition complexity mismatch | PDF p. 6, end of Sec. IV versus PDF p. 8, Conclusion | Sec. IV prints \(O(n^2\log d)\) elementary operations after including Euclid's algorithm; the Conclusion prints \(O(n^2)\). They agree only under an additional fixed-\(d\) reading that is not stated there. |
| negative zero-column count | PDF p. 6, paragraph after Eq. (13) | The setup starts from \(m'\) columns and obtains a minimal \(m\), but prints that the rightmost \(m-m'\) columns are zero. This is arithmetically suspect; the likely \(m'-m\) repair is an audit inference, not source text. |
| imprecise prime-factor terminology | PDF p. 6, paragraph before Eq. (11) | Preserve “only single prime factors” and “multiple prime factors.” Do not silently relabel the cases without another source or proof. |
| Appendix B index mismatch | PDF p. 8, Appendix B, paragraph after Eq. (B1) | The sentence defining \(r_jy_j=0\) ends “for every \(k=1,\ldots,m\)” although the displayed quantities are indexed by \(j\). Treat as a minor printed index anomaly. |
| intermediate nonunique versus final unique solution | PDF p. 9, Appendix B final paragraph; PDF p. 7, Eq. (18) | No contradiction is recorded: an intermediate Smith-system solution \(x^{*\prime}\in\mathbb Z_d^n\) is “most likely not unique,” while the reduced \(x^*=Lx^{*\prime}\pmod{\bar q}\) is the claimed unique element of \(G_{\bar q}\). |

## Project application

The source is a primary algebraic reference for representing arbitrary-\(d\)
Paulis, Cliffords, and stabilizer states. A conforming implementation must
retain the phase vector in addition to the symplectic matrix, preserve the
even-\(d\) modulo-\(2d\) phase convention, use ring-safe operations at composite
\(d\), and allow more than \(n\) minimal stabilizer generators where the source
does.

The source's Eq. (13) is a useful oracle for unitary Clifford conjugation of a
stabilizer description. It is not an oracle for measurement collapse,
conditional normalization, reset, leakage/seepage, trajectory histories, or
classical detector Records. Those mechanisms require independent sources and
independent acceptance fixtures.

The direct standard-basis expansion in Theorem 1 may provide an independent
small-system state-vector reference for algebraic tests, subject to faithfully
implementing its Smith-normal and modular phase conventions. That potential
application is a project inference and is deliberately excluded from the
atomic source-only note.

Nothing in this paper licenses the inference “qutrit algebra equals leakage
support.” Here \(d=3\) means a three-level computational Hilbert space. A
leakage model additionally requires a declared computational subspace, leaked
states, transition mechanisms, observables, and return/reset rules.

The source likewise does not close PEPS/CAPEPS, GCAMPS syndrome sampling,
Born-history faithfulness, Record construction, QEC thresholds, or resource
advantage claims.

## Competing evidence and kill conditions

- A qutrit-specific Clifford quotient or representative count must be sourced
  separately. Specializing this paper to \(d=3\) does not yield a printed
  90-class entanglement quotient or executable representative set.
- A leakage claim is killed unless a separate source and implementation define
  computational/leakage sectors, transition and return channels, and relevant
  measurements. Merely choosing \(d>2\) is insufficient.
- A stabilizer-measurement or trajectory claim is killed by the absence of a
  selective instrument, Born branch masses, conditional states, resets, and
  raw-history probabilities in this source.
- A detector-Record or Record-TV claim is killed unless a separate bridge
  defines how raw measurement outcomes fold into emitted records and supplies
  the corresponding probability law.
- A PEPS/CAPEPS or tensor-network efficiency claim is killed by the absence of
  a tensor-network ansatz, contraction method, and matched benchmark here.
- A QEC performance or capacity claim is killed by the Introduction's explicit
  statement that error-correcting capacities are not the paper's focus and by
  the absence of thresholds, decoders, noise circuits, or resource data.
- A field-style composite-\(d\) implementation is killed by the unit and gcd
  conditions in Sec. IV and the Smith-normal construction in Sec. V.
- A phase-free even-\(d\) symplectic implementation is killed by Eq. (7), Eq.
  (10), and the order-\(2d\) observation after Eq. (6).
- An unrestricted graph-state-equivalence claim at composite \(d\) is killed
  by the explicit extra-condition discussion in the Introduction and Sec. V.
- An unconditional \(O(n^2)\) decomposition claim with variable \(d\) is not
  supported without resolving the printed \(O(n^2\log d)\) versus \(O(n^2)\)
  discrepancy.

## Local schema compatibility change

The pinned source uses the legacy arXiv identifier form
`quant-ph/0408190v2`. Before this review, the current-schema parser accepted
only modern numeric arXiv identifiers, so the exact source identity could not
pass admission preflight.

With explicit authorization, a minimal additive compatibility change was made
outside `src/**`, test-first:

- `tools/literature_schema.py` now accepts either the existing modern
  `arxiv:YYYY.NNNNN` form or a lowercase legacy category plus seven-digit ID,
  such as `arxiv:quant-ph/0408190`.
- The source version remains a separate mandatory `vN` field, and the HTTPS
  arXiv URI must still pin exactly that version.
- Focused fail-closed tests reject an unversioned legacy URI, a version embedded
  in `source_id`, an uppercase category, and an underscore separator.
- The RED test failed specifically because the legacy `source_id` was rejected;
  after the minimal regex change, the focused legacy set passed `5 passed, 64
  deselected`, and the complete literature-tool file passed `69 passed in
  0.32s`.

Hashes at packet-draft time:

- `tools/literature_schema.py`:
  `6ab50f261fb64e11319831cc796bad341c4c73638144ad58cdae33d080eb23e3`
- `tests/test_literature_tools.py`:
  `476bf38f53a942e18aba2a2d383fe545bdd3102020d6c1ecc4a10224cf3a4b30`

The compatibility change does not admit this note, modify the corpus manifest,
or relax artifact/audit hash verification. Admission remains a separate
independent-review decision.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_review: pending`
- arbitrary-\(d\) Pauli multiplication and commutation: `closed`
- even/odd phase distinction: `closed`
- Clifford conjugation, composition, and inversion: `closed`
- necessary and sufficient \((C,h)\) conditions: `closed`
- constructive at-most-two-qudit decomposition: `closed`
- composite-\(d\) unit/gcd/Smith-normal subtleties: `closed`
- stabilizer generator and Clifford updates: `closed`
- direct standard-basis quadratic expansion: `closed`
- stabilizer measurement/Born instrument: `missing`
- reset, histories, and emitted Record: `missing`
- leakage/seepage/return mechanism: `missing`
- PEPS/CAPEPS bridge: `missing`
- QEC thresholds, circuit-noise evidence, and matched resources: `missing`
- qutrit-specific 90-class quotient and representatives: `missing`

The audit and corresponding atomic note remain drafts pending an independent
full-source semantic review. No corpus-manifest admission is requested or made.
