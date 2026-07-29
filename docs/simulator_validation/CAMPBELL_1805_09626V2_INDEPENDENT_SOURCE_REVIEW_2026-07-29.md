# Campbell et al. 1805.09626v2 — independent source-only review

Review date: 2026-07-29  
Review scope: fixed PDF plus the candidate source note and candidate memory-depth audit named below  
Verdict: **REQUIRED REPAIRS**

This review does not accept any project conclusion as source evidence. It independently reads the
fixed PDF, reconstructs the source argument, and then compares the candidate note and audit against
that reconstruction.

## Fixed objects and provenance

| object | independently observed identity |
|---|---|
| `docs/papers/1805.09626v2.pdf` | valid unencrypted PDF 1.5; 1,748,981 bytes; 11 pages; SHA-256 `619f3a5fe047481ef1fc434255e63e0ca3428ca594805a34d9897ec0e9fb4fd5` |
| candidate source note | SHA-256 `20ebdf4b04d20e7b5040d3077766e1a2554f8c3468543201f0cb3f1d8a6b45cf` |
| candidate audit packet | SHA-256 `688f6cb9e4beb2030c16cc691e67376c2402820a1c9f31c4db9386734dd6558b` |

The PDF itself displays `arXiv:1805.09626v2 [quant-ph] 10 Jul 2018` on PDF p. 1 and
`(Dated: July 11, 2018)` on the title page. Its title and authors match the candidate note. The
candidate note's `source_sha256` and `audit_packet_sha256` match the fixed files.

The fixed PDF does **not** display the claimed journal citation `Physical Review A 98, 012142
(2018)`: full-text inspection finds neither that article number nor that journal reference.
Therefore the candidate's `publication_status = "published"`, source-identity Claim, and locator
`journal reference` are not established by the fixed source-only object.

The full eleven-page object was read. Load-bearing source pages were also visually checked from
rendered PDF pages: pp. 1–3 for identity and Eqs. (1)–(5), p. 5 for Eqs. (7)–(13), pp. 6–7 for the
fixed-memory SWAP equivalence and its scheduling qualification, and p. 9 for the generality
boundary. Pages 10–11 contain the continuation of the bibliography; no appendix or supplement is
present in the fixed PDF.

## Independent equation and notation reconstruction

| locator | independently reconstructed source statement | fidelity consequence |
|---|---|---|
| Eq. (1), PDF p. 2 | \(\rho_{SE}(0)=\rho_S(0)\otimes\rho_{E_1}\otimes\rho_{E_2}\otimes\cdots\). | The source assumes no initial \(S\)-ancilla or ancilla-ancilla correlations. |
| Eq. (2), PDF p. 2 | \(\hat H_{ij}=-\tfrac12(J_x\sigma_{ix}\sigma_{jx}+J_y\sigma_{iy}\sigma_{jy}+J_z\sigma_{iz}\sigma_{jz})\). | It is a pairwise unitary-collision Hamiltonian for either \(S\)-ancilla or AA pairs. The isotropic case is then identified with a partial SWAP. |
| Eqs. (3)–(4), PDF p. 2 | \(\hat U_1\) contains \(d\) \(S\)-ancilla collisions; \(\hat U_{n>1}\) composes the new block of \(d\) \(S\)-ancilla collisions with pairwise AA collisions spanning the prescribed block/range. | The printed operator products and their index ranges matter. The source explicitly allows arbitrary ordering within the pairwise AA product. |
| Eq. (5), PDF p. 3 | \(\mathcal D_n=\tfrac12\lVert\rho^{(1)}_{S n}-\rho^{(2)}_{S n}\rVert_1\). | A revival for at least one initial pair is sufficient for the paper's BLP diagnosis; one monotonically decaying selected pair is inconclusive. |
| Eqs. (7)–(8), PDF p. 5 | For \(d=1\), \(\Phi_1[w]=\mathcal U_{SE_1}[w]\) and \(\Phi_{n>1}[w]=\operatorname{Tr}_{E_{n-1}}\mathcal U_{SE_n}\circ\mathcal V_{E_nE_{n-1}}[w\otimes\rho_{E_n}]\). | These equations are specifically the nearest-neighbour, one-retained-ancilla update; they are not an arbitrary-\(d\) formula. |
| Eq. (9), PDF p. 5 | \(\Phi(n)=\Phi_n\circ\cdots\circ\Phi_1\) returns the joint state of \(S\) and the last collided ancilla. | This enlarged, step-dependent \(S+E_n\) state follows a composition of CPTP maps and is called Markovian by the source. |
| Eq. (10), PDF p. 5 | \(\rho_S(n)=\Lambda(n)[\rho_S(0)]=\operatorname{Tr}_{E_n}\Phi(n)[\rho_S(0)\otimes\rho_{E_1}]\). | The reduced \(S\) dynamics may remain non-Markovian even though the enlarged evolution is Markovian. |
| unnumbered \(d=2\) maps and Eq. (11), PDF p. 5 | The source explicitly constructs a tripartite \(S+\)two-ancilla CPTP update and its composition \(\Phi^{(2)}(n)\). | The \(d=2\) case is separately written; it must not be cited as though Eqs. (7)–(9) already covered arbitrary \(d\). |
| Eqs. (12)–(13), PDF p. 5 | The source prints the reduced maps \(\Lambda^{(1)}(n)\) and \(\Lambda^{(2)}(n)\) for the original collision streams. | These equations do not themselves show a fixed, repeatedly reused memory register. |
| Eqs. (14)–(17), PDF pp. 6–7 | For \(d=1\), SWAP identities transform the original stream into an equivalent representation in which \(S\) repeatedly interacts with the same memory ancilla \(E_1\), while that memory collides with fresh ancillas. | A fixed-memory-register claim requires this SWAP replay, not merely Eqs. (7)–(10). |
| Eq. (18) and following text, PDF p. 7 | A two-memory-ancilla representation is stated equivalent to Eq. (13), and a similar approach is stated for arbitrary \(d\). | The source explicitly treats \(d=1,2\); arbitrary \(d\) is a stated analogous extension, not a separately printed general \(\Phi^{(d)}\) or \(\Lambda^{(d)}\) equation. |
| final paragraph of Sec. V, PDF p. 7 | The fixed-same-ancilla construction requires \(S\) to interact with the whole memory before the intra-environment collisions. Under a different interleaving, the last \(d\) ancillas still contain the relevant correlations, but the SWAP construction no longer ensures interaction with the same ancillas throughout. | Collision scheduling is a load-bearing qualification on the fixed-memory interpretation. |

Here \(S\) is the open system; \(E_n\) is the \(n\)-th environment ancilla; \(d\) is first the AA
interaction range and is then interpreted as memory depth; \(\mathcal U\) and \(\mathcal V\) are
unitary conjugation maps; \(w\) is a physical state on the current enlarged Hilbert space;
\(\Phi_n\) is the enlarged-state CPTP step; and \(\Lambda\) is the reduced system map. For
Eqs. (7)–(10), the retained ancilla label advances from \(E_{n-1}\) to \(E_n\); a fixed ancilla
appears only in the separate SWAP-equivalent construction on pp. 6–7.

## Candidate source-note record review

| Fact ID | result | independent source-only finding |
|---|---|---|
| `campbell-source-identity` | repair | The arXiv identifier/version, title, date lines, page count, and hash are supported. The claimed PRA publication and `journal reference` locator are absent from the fixed PDF. |
| `campbell-selection-scope` | pass | The abstract and Sec. I connect finite-range AA correlations to a finite Markovian embedding. |
| `campbell-factorized-input` | pass | Eq. (1) and its following sentence support the Claim. |
| `campbell-collision-hamiltonian` | pass | Eq. (2) supports the Claim. The partial-SWAP prose is correctly restricted to \(J_x=J_y=J_z\). |
| `campbell-step-composition` | pass with precision requirement | Eqs. (3)–(4) support the high-level Claim, but any replay must preserve the printed index ranges and the source's arbitrary AA pair ordering. |
| `campbell-memory-limits` | repair | The strong-memory endpoint is specifically perfect **AA** SWAPs in the source discussion. Replace the ambiguous “perfect ancilla swaps” wording with “perfect AA swaps.” |
| `campbell-trace-distance` | pass | Eq. (5) and the following paragraphs support both sides of the diagnostic statement. |
| `campbell-memory-depth` | repair | The Claim combines two independently locatable assertions: \(d\) is reinterpreted as memory depth, and an enlarged system contains \(d\) relevant ancillas. Split them so definition and embedding size are atomic. |
| `campbell-first-order-embedding` | pass | Eqs. (7)–(10) support the Claim, provided “retained ancilla” is not read as one fixed physical ancilla across steps. |
| `campbell-higher-memory-depth` | repair | Split the explicitly constructed \(d=2\) enlarged map on p. 5 from the analogous arbitrary-\(d\) extension stated on p. 7. Their source strength and exact locators differ. |
| `campbell-generality-limit` | pass | The final two paragraphs of Sec. VII support the Claim. |
| `campbell-gap-tensor-network` | repair | The Claim bundles five independent absence claims (PEPS contraction, truncation, runtime, bond dimension, and monotonic entanglement) and is not atomic. Split the gaps. Also, a locator called “Complete source scope” must name PDF pp. 1–11, or explicitly say “scientific body, pp. 1–9”; the current `PDF page: 1–9` does not match “Complete source scope.” |

### Relations

All three current relations point to existing Fact IDs, and each `object_label` occurs as a source
concept in its referenced Claim. The predicates are semantically defensible. After the required
split of `campbell-memory-depth`, the `collision-memory-depth` relation must point to the new atomic
definition fact rather than a composite fact. No relation may be admitted until that repair leaves
all endpoints exact and non-dangling.

### Note-frontmatter consequences

The note cannot retain `read_status = "complete"`, `operation_replay_status = "complete"`, or advance
from `pending_source_only_review` while the source-identity provenance, atomicity, and replay defects
below remain. If the audit is repaired, its SHA-256 necessarily changes and the note's
`audit_packet_sha256` must be recomputed. This review does not authorize manifest admission.

## Candidate audit review

### Assigned closure rows

| row | result | required source-fidelity change |
|---|---|---|
| factorized collision input | pass | Eq. (1), p. 2 supports the row. |
| collision Hamiltonian and complexity | repair | Eqs. (2)–(4) define a Hamiltonian and collision schedule, not a source-defined “complexity” ordering. Rename the row to the source object, or split out a clearly labelled project-defined complexity ladder. It cannot be `closed` as a source complexity row. |
| memoryless and memory-bearing limits | pass with wording repair | Specify that the perfect swaps are AA swaps. The software-retention warning is correctly not treated as a source witness. |
| finite memory depth | repair | Replace “The theorem” because the source presents a construction/argument, not a theorem. Give distinct exact locators for the \(d=1\), \(d=2\), and analogous arbitrary-\(d\) statements, including the p. 7 scheduling qualification. |
| non-Markovian observable | pass | Eq. (5), p. 3 supports the positive witness and the stated failure of a one-pair negative result. |
| generality boundary | pass | Sec. VII, p. 9 supports the boundary. |

### Operation replay

The current five-row replay is **incomplete**:

1. Its fourth row inputs “joint system plus last \(d\) ancillas” but cites Eqs. (7)–(9), which are
   only the \(d=1\) construction. Split this into \(d=1\), explicit \(d=2\), and the source's
   arbitrary-\(d\) analogue, with the correct p. 5/p. 7 locators.
2. Its fifth row emits \(\Lambda^{(d)}(n)\) while citing Eqs. (10)–(13). The source prints
   \(\Lambda\), \(\Lambda^{(1)}\), and \(\Lambda^{(2)}\), not a general numbered
   \(\Lambda^{(d)}\) equation. Preserve this distinction rather than silently inventing uniform
   notation.
3. Add the missing mechanism-to-observable replay:
   same collision map and two initial \(S\) states \(\rightarrow\) two reduced states at step \(n\)
   \(\rightarrow\) Eq. (5) trace distance \(\rightarrow\) a revival is a sufficient BLP witness;
   a monotonically decaying selected pair is inconclusive.
4. Add the fixed-memory operation replay from Eqs. (14)–(18): nested original stream
   \(\rightarrow\) SWAP insertion and identities \(\rightarrow\) index movement and partial traces
   \(\rightarrow\) equality with the original reduced dynamics. Include fresh ancillas and the
   p. 7 collision-order qualification. Without this replay, the later fixed-site project
   application has no audited source bridge.
5. Refine the Eqs. (3)–(4) row to preserve the actual block indices and to avoid implying a unique
   AA product order where the source explicitly permits arbitrary pair ordering.

Therefore the audit's `read_status: complete`, `assigned-row status: closed`, and the note's
`operation_replay_status = "complete"` are premature.

### Project-application boundary

Nothing in the fixed source establishes a Quimb, PEPS, QEC Record, contraction, truncation, runtime,
or bond-dimension claim. The audit correctly places these statements in a project-application
section, but two sentences still overstate the source bridge:

- A “joint pure-state PEPS” requires extra project assumptions such as pure initial states, or an
  explicit purification/trajectory construction. Eq. (1) permits general density operators.
- Merely retaining and repeating a finite set of memory sites is not the paper's fixed-memory
  equivalence. The source construction also uses fresh ancillas, explicit memory–fresh-ancilla
  collisions, SWAPs, partial traces, and the stated collision timing. The audit later admits that
  its repeated finite set is not the paper's exact reduced map; it must therefore remove or qualify
  the earlier assertion that this is “the carrier construction corresponding to” the paper's
  embedding.

The three-level \(J_i\) ladder is a project-defined taxonomy inspired by Eq. (2), not a source
finding. It must be labelled as such and must not be counted as a closed source row. This review
makes no judgment that the Quimb or project implementation assertions are true.

## Independent finite-memory-embedding judgment

The faithful source statement is bounded as follows:

- For the paper's collision model and schedule, finite AA range \(d\) identifies a finite set of
  relevant system-environment correlations. Enlarging the evolving state to \(S\) plus the relevant
  ancillas yields a Markovian CPTP-map composition, while tracing those ancillas can leave
  non-Markovian reduced dynamics for \(S\).
- The source explicitly writes the \(d=1\) and \(d=2\) cases and states the analogous extension to
  arbitrary \(d\).
- A representation using the same fixed memory ancilla(s) throughout is a further
  SWAP-equivalence construction with fresh ancillas and a scheduling condition.
- The source does not promote this construction to arbitrary non-Markovian dynamics and supplies no
  tensor-network efficiency or entanglement guarantee.

The candidate note is broadly aligned with the first and fourth bullets, but the candidate audit
does not yet preserve the distinctions in the second and third bullets. Its current unqualified
fixed-site application is therefore not source-faithful enough for admission.

## Required repairs and admission gate

1. Remove or separately source the unsupported journal-publication metadata and Claim; under the
   present fixed-source-only scope, use only the arXiv v2 identity visible in the PDF.
2. Make the source note atomic by splitting the memory-depth definition from embedding size, the
   explicit \(d=2\) construction from the arbitrary-\(d\) analogue, and the five tensor-network
   absence claims; correct the complete-source page scope.
3. Clarify “perfect AA swaps” and preserve the exact Eq. (3)–(4) index/order semantics.
4. Repair the closure table so “complexity” is not claimed as source-closed, “theorem” is removed,
   and \(d=1\), \(d=2\), arbitrary \(d\), and the p. 7 timing qualification have exact locators.
5. Rebuild the operation replay with separate enlarged-state, reduced-state, BLP-observable, and
   fixed-memory SWAP-equivalence chains. Do not use Eqs. (7)–(9) or invented
   \(\Lambda^{(d)}\) notation as an arbitrary-\(d\) equation.
6. Recast the PEPS/fixed-site statements as explicit bounded project inferences, state the
   pure-state preconditions, and do not call finite-site reuse the paper's embedding unless the
   fresh-ancilla/SWAP/trace/timing construction is actually reproduced.
7. Recompute the audit hash in the note after repair, rerun independent source review, and only then
   decide whether `read_status`, `operation_replay_status`, and admission fields can advance.

Final status:

- independent full-text read: `complete`
- independent review artifact: `persisted`
- candidate source-note/audit admission: `FAIL — REQUIRED REPAIRS`
