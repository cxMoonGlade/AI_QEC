# CAPEPS research-state recovery checkpoint

Date: 2026-07-27

Checkpoint status: `COMPLETE__NARROW_GCAPEPS_MATHEMATICAL_PACKET`

Scientific closure: `RESCOPED_TO_NARROW_GCAPEPS_MATHEMATICAL_FEASIBILITY`

Allowed work: the minimum source checks needed for a GCAMPS-to-GCAPEPS
mathematical translation; exact definitions, lemmas, closure proofs, worst-case
bond bounds, adversarial mathematical review, and repair of this evidence packet.

Blocked work: GCAPEPS efficiency claims, target experiment/code, Record-law or
full-QEC-instrument expansion, broad comparator literature work, and manuscript
claims beyond the proved finite-lattice theorem.

This is the single recovery pointer for the ongoing GCAPEPS mathematical note.
It records the current reasoning state that must not be reconstructed from chat
memory. Read `docs/SIMULATOR.md`, then this file, then the frozen theorem and
independent-review artifacts named below before resuming the task. The older
`CAPEPS_THEORY_FIX_EVIDENCE_REOPEN_2026-07-27.md` belongs to the suspended broad
programme and is not a continuation instruction.

## User-rescoped objective — binding from 2026-07-27

The user explicitly narrowed the project: **construct only the GCAMPS-style
GCAPEPS generalization and prove that it is mathematically feasible.** The
previous measurement--reset--Record efficiency programme is suspended context,
not the active objective.

The active theorem target is therefore:

\[
\boxed{
|\Psi\rangle=C|\phi\rangle,\qquad |\phi\rangle\in\mathrm{PEPS}(G,\mathbf D),
}
\]

on a finite two-dimensional graph \(G\), together with exact closure under the
GCAMPS algebraic operations and explicit finite worst-case bond bounds. The
proof must separate:

1. tensor-network-topology-independent Clifford-frame identities inherited
   from GCAMPS;
2. PEPS/PEPO closure of the pulled-back residual operation;
3. the optional paired Clifford-refactor identity from its PEPS bond bound; and
4. mathematical existence from any claim of low bond, efficient contraction,
   scalable optimization, or advantage over full PEPS.

The intended name in the active proof packet is **GCAPEPS**. Existing files may
still use the earlier project label CAPEPS; do not interpret that historical
name as a broader active scope.

### Current durable proof artifact

- theorem packet:
  `docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`
- current SHA-256:
  `7f5ec9c7c3dac2da7c377c0958f7eafc104d2da19b59350e1a7c336cc1cc10dc`
- review status: `MATHEMATICAL_CONTENT_REVIEWED_PASS`
- durable independent review:
  `docs/simulator_validation/GCAPEPS_MATHEMATICAL_FEASIBILITY_INDEPENDENT_REVIEW_2026-07-27.md`,
  SHA-256 `23bac8a83cbca57d9b88fffc4f9ff8e3ded1578045ec9663b4998c00c76f47c7`
- review history: three independent mathematical angles found the same
  repairable Lemma-3 defect in the initial draft: a common nonidentity routing
  factor was replaced by identity, the root copy constraint was underspecified,
  and the single-vertex tree was omitted. The candidate above repairs all three,
  defines the active set, and then received two strict post-repair PASS verdicts.
  The adversarial reviewer separately confirmed the final artifact hash after
  the Eq. (17) scope clarification; no mathematical or artifact blocker remains.
- central project-derived result: an \(r\)-term pulled-back Pauli-product sum
  has a tree-routed PEPO of bond at most \(r\), and exact PEPO application maps
  \(D_e\mapsto D'_e\le rD_e\) on routed edges. A qubit Pauli rotation has
  \(r\le2\).
- explicit nonclaim: repeated updates may make bonds exponential; this packet
  establishes exact finite representability, not efficient contraction or an
  advantage over full PEPS.

### Current durable manuscript artifacts

- technical note:
  `docs/simulator_validation/GCAPEPS_TECHNICAL_NOTE_DRAFT_2026-07-27.md`,
  SHA-256 `35b8040caa08fd86b49dbca4e71442b53592c9ca22c35f3061397c73976a2261`,
  status `MATHEMATICAL_CORE_REVIEWED__CONSISTENCY_REVIEW_PASS`;
- manuscript consistency review:
  `docs/simulator_validation/GCAPEPS_TECHNICAL_NOTE_INDEPENDENT_CONSISTENCY_REVIEW_2026-07-27.md`,
  SHA-256 `b06fe659e96c07add0f16efafe04eafafcf02bbc232bff89cb5cf19ab8a526b0`,
  final decision `PASS` after closing the missing-sidecar artifact blocker;
- mathematical architecture:
  `docs/simulator_validation/GCAPEPS_MATHEMATICAL_ARCHITECTURE_2026-07-27.md`,
  SHA-256 `a91e8631221c63e9957abe2f9b1907433c9628b70cffa122b335b7219a0a8532`;
- current-scope pointer:
  `docs/simulator_validation/GCAPEPS_CURRENT_MANUSCRIPT_POINTER_2026-07-27.md`,
  SHA-256 `c0e572c530451d9bacba2f55c871248af59cec47c1f6d14892aed48e9bf44ec9`.

No source code, experiment, Record/QEC instrument, or efficiency programme was
added in this work unit. The older broad CAPEPS/XZZX manuscript and architecture
remain historical files and were not overwritten.

### Current exact continuation order

1. Completed: the short GCAPEPS mathematical technical note has passed
   independent consistency review.
2. Completed: the active source set is restricted to GCAMPS, its direct
   continuation, finite PEPS, and PEPS contraction hardness.
3. Completed: the theorem, reviews, note, architecture, pointer, checkpoint,
   four PDFs, four reading notes, and four audits were copied with `cp` into the
   evidence bundle; both manifests passed `sha256sum -c --quiet`.
4. Current terminal instruction: stop. Do not resume Record/QEC experiments,
   broad disconfirmation reading, implementation, or efficiency claims unless
   the user explicitly widens the scope in a later request.

### Evidence-bundle synchronization

The minimal current packet is
`docs/CAPEPS_EVIDENCE_BUNDLE_2026-07-27/00_CURRENT_GCAPEPS_MATHEMATICAL_PACKET/`.
It contains only the current manuscript/proof/review chain and the four-source
literature chain. All entries are copies; no canonical source was moved. Its
own `MANIFEST.sha256` and the bundle-root `MANIFEST.sha256` were regenerated and
verified successfully after assembly.

## Superseded broader question — retained only as history

The previously studied question was:

\[
\text{Can a Clifford frame plus PEPS residual preserve the complete declared}
\quad\text{measurement--reset--Record law more efficiently than matched full PEPS?}
\]

The candidate representation is branch indexed,

\[
\lvert\psi_h\rangle=C_h\lvert\phi_h\rangle,
\]

with the Clifford frame represented by a stabilizer tableau and only the
non-stabilizer residual represented by PEPS. Efficiency is a hypothesis, not a
deduction from the size of the Clifford skeleton.

## Superseded broad-programme scientific boundary — archive only

Everything from this heading through the superseded continuation order below is
retained only to preserve research provenance. It must not drive current work.

1. Harper et al., arXiv:2605.29514v1, is the direct orthodox continuation of
   GCAMPS and the closest predecessor. It already applies
   \(C\lvert\mathrm{MPS}\rangle\) to repeated rotated-surface-code syndrome
   extraction with coherent \(ZZ\) crosstalk for \(d=3,5,7,9\), and reports
   calculations up to \(\chi_{\max}=32\). Therefore this project must not claim
   the first hybrid stabilizer--tensor-network simulation of coherent QEC.
2. That source does not supply a PEPS residual, an explicit
   measurement--reset transaction, a full Born prefix/branch-mass ledger, a
   detector Record law, or a matched full-PEPS resource comparison. These are
   candidate differentiators only; their novelty and correctness remain open.
3. The original GCAMPS algebra closes only the MPS frame/residual mechanism. The
   repository now contains an `[ours/implemented]` all-qubit, untruncated
   engineering-mechanics prototype of \(C\lvert\mathrm{PEPS}\rangle\), with a
   Stim frame, dense/Quimb residual, coherent signed-Pauli pullback, exact local
   refactorization, ordered raw conditional branch log mass, and computational-
   basis \(Z\) measure-reset. It remains scientifically unclosed: its
   `MeasurementEvent` is not `RecordBatch`, and it has no complete multi-round
   detector/observable Record, leakage/qutrit semantics, controlled finite-bond
   approximation, target scaling result, or production-faithfulness claim. The
   two-dimensional extension is not source-established, and the existing
   full-PEPS preregistration does not authorize a CAPEPS target experiment.
4. The original stabilizer tensor-network source supplies selective Pauli
   measurement primitives, but not a reset/Record instrument or CAPEPS/full-PEPS
   comparison. Magic-state-injected STN and general exact Born-sampling work are
   now mandatory disconfirmation sources.
5. General PEPS contraction hardness and local-observable approximation theorems
   do not establish either failure or efficiency on the bounded XZZX fixture.
6. The existing 25-qubit PEPS result is a baseline only. It must not be described
   as the complete QEC result.

At the time of that broader programme, its provisional paper centre was:

\[
\boxed{\text{GCAMPS-inspired }C\lvert\mathrm{PEPS}\rangle
+\text{ explicit QEC instrument}
+\text{ raw/Record correctness}}
\]

Whether this centre survives the remaining literature closure and falsification
is not yet decided.

## Historical admitted source packets from the broad programme

All entries below are source-only evidence. Admission does not imply that a
project theorem or implementation exists.

| source | durable artifacts | admitted conclusion and boundary |
|---|---|---|
| GCAMPS, arXiv:2511.06672v2 | PDF SHA `880c44e25e9c1fd589a75ca5e824e58a2436c0c35a7ee7dddebbb61d439a0c42`; note SHA `770bad822875f1e301beab5627d4e395daea29f5b74ffaacc7ffffdd4e570f02`; formula audit SHA `0851e0c193d47df5ac789c6fa398a4bd9357bc04611f148aa59d77928a6a6cea` | Exact MPS Clifford-frame/residual skeleton; several coefficient-solver and optimizer details remain source-local gaps. |
| Harper hybrid QEC, arXiv:2605.29514v1 | PDF SHA `c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd`; note SHA `980501ee4e824c5e1fd3858d2724e2f48ce984565c7b630bf916a52fab351311`; audit SHA `e8731498a5efc2e8288826cebf4c85e7357fc569d2ba9256bfc8610048adc48d`; round-2 review SHA `1e9c7bcebc7b8763a23ea86c0c656b7092fe3f26013623af652ab85a9cfb5781` | Direct GCAMPS-in-QEC predecessor; MPS only and no complete reset/Record law or matched PEPS comparison. |
| Kim et al., arXiv:2607.03939v1 | note SHA `d2e484753b717f4639ca7c7ffd15591ad89b0547c375e3d8262cc4a67ac9c589`; audit SHA `85ea87de03027d8ddee61bea3bcdc952acbb7faeced9c393720cd8e689bd2613`; round-2 review SHA `99e4db26c34834564b294dfe7a08cec2d744af0883a2db670f4b454a8cf4c9a6` | The active paired update \((H,\lvert\psi\rangle)\mapsto(CHC^\dagger,C\lvert\psi\rangle)\) is internally consistent. The number 90 is a one-sided coset count, not a double-sided class count. Exact theorem is restricted to the stated AKLT setup; no PEPS/QEC/Record theorem follows. |
| Masot-Llima et al., arXiv:2602.15942v2 | note SHA `2afe4b4d19b3b9e0331279476e544559cdd5b1674e8be1b2153f1222c719e5c5`; audit SHA `49cc95ccf98d83dd16bb342cca20c28861a7783753162fbc62e942033ad51986` | The printed theorem is retained as `FAIL_AS_PRINTED` because of proof defects and an explicit counterexample. Its count 20 is one-sided, not the printed double-sided local-equivalence count. |
| Stabilizer Tensor Networks, PRL 133, 230601 | article SHA `7630570…46c56b`; supplement SHA `5d9dcbd…276b2d1`; note SHA `aeb6682c2235049a28e7175a53d7499cabb8c9191658f41fd981b698e2d145d6`; audit SHA `6cf214d3a265e8f2c3632a4fe1a97aae1a6c69b4f89d9c32fe5aa857182b992d` | Measurement must split the \(\hat n\ne0\) and \(\hat n=0\) cases; the uniform lemma is undefined at zero. Multi-term treatment is formal factorization and the backend is MPS, with no reset/Record/PEPS matched comparison. |
| Schwarz et al., arXiv:1606.06301v2 | note SHA `596aa77b0c0488babb8fe5a510edb050f40ab69102235c418664c2e8d0c2d33e`; independent review SHA `8a9b69e1e9cd93db9469a295801b1336ba7f4dd841a28db30ee89d32f90d1bd2` | The theorem concerns normalized local scalar expectations under injectivity, uniformly gapped prefix parent Hamiltonians, controlled condition number, and constant support. It is not a global-fidelity, truncation, instrument, Record, or CAPEPS-efficiency theorem. |
| Czarnik--Dziarmaga--Corboz, arXiv:1811.05497v2 | PDF SHA `a29c4bf23e381c50cae91a708456d6240792302bf1c0e127348cd2c6fdc5639c`; promoted note SHA `21e424ee69715a7899577e3606187677d711705cc9ff293eed57fe4069adb2fb`; audit SHA `8cbca6a0b180a78ac566ec3bf31b211d32e7a53a427f2b586de598e2b8bc71d6`; independent PASS SHA `547fa63d5d830f277c002e3e6874ba51d0541f0eb9ed92e45bfa7302ca16ff6e` | Supports an infinite-iPEPS local gate bond-growth/compression mechanism and selected Ising evidence only. Finite-\(\chi\) CTMRG remains approximate; no QEC instrument, reset, Born history, Record, Clifford/CAPEPS, or matched resource result follows. |
| Hostens--Dehaene--De Moor, quant-ph/0408190v2 | PDF SHA `b48cf81d89050ccf9372d5be713c098088fd3a0d371e9be2a9901d09ef07c831`; promoted note SHA `8aa5036b651b3386c636b4711c237d289745b97c872feb5dad6382602a58dce6`; promoted audit SHA `80eac75b50ff59b4008dd0f288ab5080b84e704bb8ad45996c480bf9a1df8a74`; independent PASS SHA `e98dd6aa8df1259da77ffd94c77fb8d70a8e041d1f6043fc3ebfa6991491224b` | Closes arbitrary-\(d\) Pauli/Clifford/stabilizer modular algebra at the cited source scope. It does not supply leakage-sector semantics, selective measurement/reset/Record, MPS/PEPS/CAPEPS, QEC resources, a qutrit local-equivalence catalogue, or the 90-count. |

The abbreviated STN PDF hashes above must be replaced by full hashes when the
bundle inventory is next regenerated; the note/audit hashes are complete and
are the operative source pointers in this checkpoint.

## Historical draft or blocked packets from the broad programme

| source | current durable state | exact next gate |
|---|---|---|
| Vanderstraeten et al., arXiv:2110.12726v2 | First review `FAIL`, SHA `56e2d675ff98a692d99332c300c8d7471c75585c3fad866f05fe12463715b730`; round-2 review `FAIL_ONE_NEW_NOTATION_BLOCKER`, SHA `9fba9ddeeba7aa67e0c712fae48ac093e3eb93c2eca6365c4756b50ca38828c2`; round-3 review `FAIL_THREE_AUDIT_BLOCKERS`, SHA `48efeecb59cc9082ea5e2ba53f20c16584d9423d09b3aa5e5181d2e8af2e3bee`. The three Round-3 blockers were mechanically repaired in report SHA `e3e3b0b2d0144353209597dc9b23d7b36a1c2b3e51f2afd3e6cf39634265cc95`; current draft note SHA `9b51b118037d3f8696b7b5c0ab03ab6dcc1f28e6f3f4afd7efd52cd630c5d017`; audit SHA `4cd67341564d8f8354252331f68e07abc35fad557dccbc01c2c7b9ca1ed26046`. Status-toggle-only preflight reports 21 facts, 7 gaps, and 5 relations. | Audit now explicitly qualifies PEPS virtual bond dimension \(D=5\), separates generic \(M,\widetilde M\) from Hermitian ket/bra \(M,\bar M\), and preserves \(N\)-point, Eq. (62) tensors \(N_1\ldots N_L\), and benchmark window-size \(N\). This is a repair record, not a review verdict: the note remains `draft_pending_review`, requires a fresh independent source-first rereview, and must not be admitted yet. |
| Nakhl et al., arXiv:2411.12482v2 | Draft note SHA `38cf74639359d76a4b76832fa324e831aad23e7eb461e195121b4318b8cefd79`; audit SHA `5db0b9d8eec2ce4d08d05effb6f9085f2f3d1a480f6142b6bedfb346a8a05deb`; source PDF SHA `86de97a1ac18ac9c98272e5180e222115c0590d5cd0759a1eb7fd829ab81eaee`. Status-toggle-only strict preflight passed with 17 paper facts and 11 source-local gaps. Independent review `FAIL / admission BLOCKED`, report SHA `d09b9a3ef4b6e678731b4424b41e65759bc2a5dd9efbd8163cefbb5a7ea86257`. | Repair all seven reviewed blocker classes before rereview: missing p. 4 bounded-STN contradiction and p. 9 \(k=N\) ambiguity; incomplete/conflated notation; quantitatively over-strong replay status; fact atomicity/locator spill; stale CAPEPS project boundary; unbound competing-source statements; and semantically misleading relations. The stable source conclusion remains STN coefficient-MPS plus magic injection/deferred projection, not \(C\lvert\mathrm{MPS}\rangle\) or \(C\lvert\mathrm{PEPS}\rangle\), with no complete reset/Record or matched full-PEPS result. Do not admit. |
| Bravyi--Gosset--Liu, arXiv:2112.08499v2 | Draft note SHA `403bdbdb691b965e09263360fc436c66883eb3010a7aea6b0c11027cab38e8b0`; audit SHA `b909593a3c3f24d7ecefcfc5ea2f1c2aa572ee354517afcd007c1e3da0c38049`; PDF SHA `4743d2f0ed7de44f0da83ca875fb69dd15378cecfb54ef368da93d81580c68c6`. Status-toggle-only strict preflight passed, but independent review `FAIL / DO NOT ADMIT`, report SHA `39f9a69385e7808c03a0504e4dea8792d6a57b805531e80e2cb52d3dc43f14f2`. | Repair three blocker classes before rereview: disclose Supplemental p. 8 Eq. (22)'s load-bearing `U_t|psi_t>` typo without upgrading the corrected line to a source theorem; add the p. 10 fixed-`0^n` CoTenGra rehearse assumption; split the identified positive facts and gaps into atomic records and remove duplicated reset/channel prose. The stable source conclusion remains exact marginal-free Born sampling with \(Q_t=P_t\), while the adaptive extension requires measured qubits to remain untouched and supplies no conditional quantum state, reset, QEC Record fold, CAPEPS, matched full PEPS, or measured peak-memory evidence. |
| Li et al., arXiv:2508.14670v1 | PDF present | Clean source-only packet and independent review required before any multi-qutrit backend claim. |

## Historical disconfirmation-source queue from the broad programme

These files were downloaded on 2026-07-27, have not yet been admitted, and may
not be cited as closed evidence.

| source | local PDF SHA-256 | why it is load bearing |
|---|---|---|
| Nakhl et al., arXiv:2411.12482v2, *Stabilizer Tensor Networks with Magic State Injection* | `86de97a1ac18ac9c98272e5180e222115c0590d5cd0759a1eb7fd829ab81eaee` | Direct hybrid-STN competitor that may narrow the claimed non-Clifford simulation contribution. Clean deep read is assigned. |
| Bravyi--Gosset--Liu, arXiv:2112.08499v2, *How to simulate quantum measurement without computing marginals* | `4743d2f0ed7de44f0da83ca875fb69dd15378cecfb54ef368da93d81580c68c6` | General exact Born sampler using amplitude queries, including tensor-network and low-rank stabilizer applications; may narrow measurement-sampling claims. |
| Kam et al., arXiv:2603.05474v2, *Spatiotemporal Pauli processes* | `3929443fb4587fefdd675dd611e05c9ce41ec4d8d0aea774bc8efb8bb0407c80` | Defines a twirled multi-time joint Pauli-trajectory law and surface-code demonstrations; load bearing for the twirled-tableau/Record comparator. |
| Zhang--Gopalakrishnan--Styliaris, arXiv:2405.09615v3, *Characterizing MPS and PEPS Preparable via Measurement and Feedback* | `5030e788bc1b7657d1c968ed17755c2869c72519025f80def154445cc3e7c67b` | Name-adjacent PEPS/measurement/Clifford work that must be ruled in or out before a novelty statement, even though its apparent scope is state preparation rather than classical CAPEPS simulation. |

The legacy coherent-surface-code source arXiv:1710.02270 and the current legacy
note for arXiv:2603.05474 must also be re-evaluated under the clean source-only
workflow; a legacy summary is not evidence.

## Historical external-search state from the broad programme

External disconfirmation search has started but is not exhaustive. The academic
subdomain was enumerated before search. Search families executed on 2026-07-27
included:

- `Clifford augmented PEPS stabilizer tableau residual PEPS`
- `C|PEPS Clifford augmented tensor network simulation`
- `measurement reset Born branch mass multi-round syndrome Record tensor network`
- `exact quantum measurement sampling tensor network stabilizer marginals`
- `Pauli twirl multi-time Record surface code tensor network`
- exact-name search for `"Clifford-Augmented PEPS"` and `CAPEPS`

No direct prior method named Clifford-Augmented PEPS was found in these searches,
but that is search evidence only, not a priority or absence proof. The four
new sources above were surfaced by the disconfirmation search and must be read
before the search ledger can close.

## Historical corpus snapshot from the broad programme

The last validated local RAG artifact contains:

- `note_count = 44`
- `paper_fact_count = 652`
- `chunk_count = 652`
- `corpus_status = active`
- `corpus_sha256 = 9e7f5329166a8230db5274125978ecb67b868c21be68ca37d79886bf4fff823c`
- `CURRENT_CORPUS.toml` file SHA
  `3a9445ccffdc2fbc21f4f2b3ce3e13f021d072a060d41ea87f12b1afcb29cd29`

RAG, KG, and the concept index were rebuilt after Hostens admission. The KG
contains 154 source-located edges with zero dangling edges. `tests/test_literature_tools.py` passed
`69/69`. The index must be rebuilt and this section updated after every new
admission.

## Superseded continuation order — DO NOT EXECUTE

The numbered list below is void under the binding user-rescoped objective. It is
kept only as an audit trail of the suspended programme.

1. Obtain a fresh round-3 independent rereview of twice-repaired
   Vanderstraeten; admit only after PASS.
2. Czarnik is admitted; preserve its infinite-iPEPS-only boundary in every
   downstream claim.
3. Finish Hostens plus the legacy-arXiv schema regression, then independently
   review it.
4. Independently review the completed arXiv:2411.12482v2 draft; then deep-read
   and independently review arXiv:2112.08499v2, arXiv:2603.05474v2, and
   arXiv:2405.09615v3.
5. Create and review the arXiv:2508.14670v1 multi-qutrit packet.
6. Rebuild RAG, KG, and concept index; run the literature-tool test suite.
7. Update the evidence closure ledger and the copied evidence bundle using
   `cp`, never `mv`; regenerate its manifest.
8. Only when every load-bearing row is `closed` or an explicit
   `confirmed-literature-gap`, run `stress-test-claim`.
9. Only after a passing stress test may the manuscript architecture and prose be
   rewritten. Experiments remain separately gated by preregistration.

## Anti-loss write discipline

From this checkpoint onward:

1. Every completed source read writes a note and audit before another source is
   opened.
2. Every independent review writes a durable PASS/FAIL report with exact hashes.
3. Every promotion or failure updates this checkpoint in the same work unit.
4. Every new download records exact version, path, and SHA here before reading.
5. Every corpus admission updates the corpus snapshot and test result here.
6. Any change to the scientific boundary is written here before it is used in
   paper prose or delegated work.
7. After context compaction, resume from this file; do not repeat searches or
   infer status from chat summaries.

This checkpoint is operational memory, not scientific evidence. Primary PDFs,
source-only notes, audits, independent reviews, and validated corpus records
remain the evidence.
