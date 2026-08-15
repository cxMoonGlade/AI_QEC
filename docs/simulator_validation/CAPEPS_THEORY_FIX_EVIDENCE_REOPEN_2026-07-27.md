# CAPEPS theory-fix evidence reopen packet

Date: 2026-07-27

Closure status: `open`

Theory-fix decision: `REOPEN_EVIDENCE`

Stress-test status: `NOT_RUN__LITERATURE_PRECONDITION_OPEN`

This packet freezes the claim and records the evidence repair initiated after
the prior CAPEPS rewrite was incorrectly treated as more strongly verified
than its source closure allowed. It is a working closure packet, not a
scientific acceptance, preregistration, code permission, or experiment
authorization.

## Recovery pointer

The live continuation state, completed source packets, exact hashes, pending
reviews, newly acquired disconfirmation sources, and ordered next actions are
maintained in
`CAPEPS_RESEARCH_STATE_CHECKPOINT_2026-07-27.md`. Read that checkpoint after
any context compaction. This reopen packet contains the frozen claim and
coverage structure, but several source-state rows below reflect the moment of
reopening and must not override the newer checkpoint.

## Frozen claim

| required field | frozen value |
|---|---|
| decision / consequence | Decide whether a Clifford-frame plus PEPS-residual representation can preserve the complete declared measurement--reset--Record law more efficiently than a matched full-PEPS representation. A positive answer would authorize only a later preregistration, not a result claim. |
| mechanism | Represent each branch as \(C_h\lvert\phi_h\rangle\), store \(C_h\) in a stabilizer tableau, store the non-stabilizer residual in a PEPS, pull physical non-Clifford operations and projectors through the frame, and update the frame/residual pair exactly before any declared approximation. |
| observable / Record object | Population raw-history law, the frozen detector/observable Record fold, selected conditional states, reset checks, maximum state/environment bond, runtime, and peak host/device memory. |
| mechanism-to-observable bridge | Exact untruncated frame/residual identities plus Born branch masses must reproduce the same raw instrument as an independent dense reference; a frozen classical fold then maps the raw law to the Record law. Any finite-bond or approximate-contraction bridge requires an independently reviewed error argument and direct numerical falsifier. |
| predicted direction / scale | Unknown. CAPEPS is hypothesized to reduce residual bond, runtime, or memory on Clifford-dominated coherent XZZX workloads, but measurement branching, pullback support growth, PEPS environments, and optimizer overhead may remove or reverse the advantage. |
| alternative formulations / invariants | Dense exact instrument; matched full PEPS; Clifford-augmented MPS mechanism control; Pauli-twirled tableau different-channel baseline; physical-ray equality under paired \(Q,Q^\dagger\) updates; raw branch-mass conservation; invariant Record fold. |
| possible no-go | General PEPS contraction hardness; absence of an MPS-like canonical form for generic PEPS; measurement-induced residual spreading; unproved finite-bond-to-Record bound; topology-dependent optimizer cost; no direct prior CAPEPS implementation established. |
| implementation target | Repository CAPEPS research carrier and a future neutral XZZX instrument fixture. No target code or execution is authorized while this packet is open. |

Why the claim is seductive: the Clifford skeleton is large and cheap in a
tableau, so moving it out of a tensor network appears likely to save bond
dimension. That intuition is not an observable-level efficiency result and
does not account for pulled-back support, branching, PEPS contraction, or
optimizer overhead.

## Coverage ledger

Allowed row statuses are only `closed`, `missing`, `ours-inference-only`,
`contradicted`, and `confirmed-literature-gap`.

| load-bearing row | required object | local evidence queried | external search queried | source / reading note | source location | status | implication |
|---|---|---|---|---|---|---|---|
| Clifford-frame residual mechanism | Exact \(C\lvert\mathrm{MPS}\rangle\) invariant, Clifford update, signed pullback, paired refactor | RAG queries listed below; artifact-verified GCAMPS and Liu--Clark notes; Harper hybrid-QEC source reread but fresh independent admission pending | pending | `harper_gcamps_2511.06672v2.md`; Harper hybrid draft `harper_hybrid_surface_code_2605.29514v1_source_review.md`; `liu_clark_clifford_augmented_mps_2412.17209v2_source_review.md` | GCAMPS Secs. 2.2--3, Fig. 3; Harper hybrid Sec. IV.A Eq. (7); Liu--Clark Sec. II | `closed` for the MPS residual algebra only | Does not establish a PEPS residual, complete instrument, or CAPEPS efficiency; Harper's adjacent-QEC row remains pending independent admission. |
| Direct Clifford-frame plus PEPS-residual precedent | Full prior method or implementation | Local RAG finds Harper's PEPS layout only as future work | pending | no admitted direct CAPEPS source | Harper hybrid conclusion, PDF p. 7 | `ours-inference-only` | CAPEPS must remain `[ours/proposed]`; no priority claim is allowed. |
| Selective measurement and ordered Born law | Outcome probabilities, conditional states, ordered sequential law | Artifact-verified Czajkowski--Grilo note; Harper hybrid-QEC draft supplies only a high-level projective-measurement pull-through pending fresh admission | pending | `czajkowski_grilo_sequential_measurements_2101.08313_source_review.md`; Harper hybrid draft | Czajkowski--Grilo Sec. 2.2 Eq. (1), Sec. 3.1 Eq. (9); Harper Sec. IV.A | `closed` for the general primitive | Does not by itself close a CAPEPS implementation or finite-bond error bridge; Harper does not print the outcome-resolved instrument. |
| Reset and XZZX Record components | Physical reset/re-preparation, XZZX geometry, consecutive-round defect | Artifact-verified Ghosh, Bonilla Ataides, and Darmawan notes | pending | current-corpus notes for arXiv:1306.0925v2, 2009.07851v3, and 2104.09539v2 | Ghosh Fig. 1; Bonilla Ataides Figs. 1 and 5; Darmawan Sec. II.B and Fig. 6 | `closed` for cited components | Absolute target columns, offsets, and full neutral instrument remain project inputs. |
| Complete CAPEPS raw/Record law | Exact target fixture plus independent equality of raw branch masses, conditional states, reset action, and Record fold | No admitted source or completed target evidence | pending | none | none | `ours-inference-only` | Must remain a proposed correctness protocol. |
| Qubit disentangler candidate quotient | Complete post-local 20-key design and independent all-720 reconstruction | Artifact-verified Chang note plus project reconstruction | pending | `chang_clifford_disentanglers_2606.12056v1_source_review.md` | Chang Eq. (10), Algorithms 1--2, Theorem 1 | `closed` only for the admitted qubit source facts | FOCUS-dependent and project-enumeration gates require separate durable artifacts and review. |
| Qutrit 90-count and phase lift | Exact qutrit quotient/count and modular phase conventions | GCAMPS reports 90; Kim and Hostens source notes absent | pending | arXiv:2607.03939v1 and quant-ph/0408190v2 require deep read | assigned source locators pending verification | `missing` | All qutrit/SDIM conclusions remain blocked. |
| Double-sided quotient disconfirmation | Exact Masot-Llima claim, Córcoles local-equivalence classes, self-contained counterexample | Source notes absent; project CNOT counterexample exists | pending | arXiv:2602.15942v2 and 1210.7011v2 require deep read | assigned source locators pending verification | `missing` | The project counterexample may remain `[ours]`; source attribution and four-class conclusion cannot yet carry design weight. |
| Rényi-2 / local disentangler objective | Source definition and limits of the optimization objective | Liu--Clark admitted; Qian source note absent | pending | arXiv:2412.17209v2 admitted; 2405.09217v2 requires deep read | Liu--Clark Sec. IV.A Eq. (19); Qian locator pending verification | `missing` | Metric owner/value test and Qian attribution remain blocked. |
| Exact finite-network PEPS fidelity | Normalized whole-network fidelity objective | Artifact-verified Evenbly note | pending | `evenbly_closed_loop_truncation_1801.05390_source_review.md` | Sec. V Eq. (12) | `closed` for the source-defined objective | It is not automatically a complete cq-instrument or Record-TV certificate. |
| Finite-bond / approximate-contraction to Record error | A theorem or independently reviewed derivation from state/environment approximations to the declared Record object | No admitted source or independent proof | pending | Schwarz, Vanderstraeten, and Czarnik sources require deep read; project lemma lacks independent review | locators pending verification | `missing` | Scalable correctness and certificate language remain blocked. |
| PEPS contraction no-go boundary | Exact general complexity boundary and finite-PEPS limitations | Artifact-verified Schuch and Lubasch notes | pending | current-corpus Schuch and Lubasch notes | Schuch VOR pp. 2--3; Lubasch Secs. II--III | `closed` for the stated worst-case/background facts | Does not prove the bounded XZZX fixture is hard or CAPEPS is faster. |
| Stabilizer tensor-network alternative | Exact scope of the stabilizer-tensor-network construction | Only a legacy note exists | pending | arXiv:2403.08724v2 requires a clean source-only reread | locator pending verification | `missing` | Cannot use the legacy note as current evidence or make a comparative novelty claim. |
| Multi-qutrit Clifford rule set | Exact rule set and relation to the required tableau backend | PDF exists; no admitted source note | pending | arXiv:2508.14670v1 requires deep read | locator pending verification | `missing` | No qutrit backend/correctness transfer is allowed. |
| Matched CAPEPS versus full-PEPS efficiency | Frozen same-channel estimand, correctness gate, timing/memory protocol, repetitions, uncertainty, and measured result | No admitted literature theorem and no completed target run | pending | project protocol only | none | `ours-inference-only` | Efficiency remains a hypothesis; no winner or scaling statement is allowed. |

## Known unclosed source objects

| source | required version | object state at reopen | note/admission state |
|---|---|---|---|
| Masot-Llima and Garcia-Saez, stabilizer tensor networks | arXiv:2403.08724v2 | noncanonical cached PDF and legacy note | clean source-only note required |
| Qian, Huang, and Qin | arXiv:2405.09217v2 | PDF/provenance/text present | no current note or admission |
| Kim, Oh, and Kim | arXiv:2607.03939v1 | PDF/provenance/text present | no current note or admission |
| Hostens, Dehaene, and De Moor | quant-ph/0408190v2 | exact PDF added only to evidence bundle | no current note or admission |
| Masot-Llima et al., limits of Clifford disentangling | arXiv:2602.15942v2 | canonical cache had v1; exact v2 added only to evidence bundle | no current note or admission |
| Córcoles et al. | arXiv:1210.7011v2 | exact PDF added only to evidence bundle | no current note or admission |
| Czarnik, Dziarmaga, and Corboz | arXiv:1811.05497v2 | unversioned bundle alias verified byte-equal to v2 | no current note or admission |
| Li et al. | arXiv:2508.14670v1 | PDF/provenance/text present | no current note or admission |
| Schwarz, Buerschaper, and Eisert | arXiv:1606.06301v2 | exact PDF added only to evidence bundle | no current note or admission |
| Vanderstraeten et al. | arXiv:2110.12726v2 | exact PDF added only to evidence bundle | no current note or admission |
| Harper et al., hybrid GCAMPS surface-code application | arXiv:2605.29514v1 | exact PDF, note, and audit present; main-agent full read and visual check complete | prior admission withdrawn because no durable independent-review report exists; fresh review required |

## Anomaly ledger

| contrary fact / ambiguity | source and exact location | affected object | implication | status / action |
|---|---|---|---|---|
| The closest admitted hybrid-QEC source uses \(C\lvert\mathrm{MPS}\rangle\) and lists PEPS only as future work. | Harper et al. 2605.29514v1, conclusion, PDF p. 7 | Direct CAPEPS precedent | The PEPS bridge is project-proposed, not source-established. | preserve; external search required |
| The GCAMPS source closes the algebraic skeleton but leaves coefficient-solver and optimizer details unspecified. | `GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md` assigned-row and operation-replay tables | Executable reproduction and optimizer | Do not infer a complete implementation specification from the paper. | preserve as source-local gaps |
| The closure used arXiv:2602.15942v2 while the canonical cache held v1. | repository artifact inventory, 2026-07-27 | Double-sided quotient attribution | Exact v2 must be acquired and reread; v1 evidence cannot substitute. | source acquisition in progress |
| The current disentangler packet calls some rows closed while explicitly stating that their source notes are open. | `CAPEPS_DISENTANGLER_THEORY_FIRST_CLOSURE_2026-07-27.md`, coverage/admission ledger | Closure semantics | Normalize all such rows to `missing` until deep read and admission. | repair after source closure |
| The project finite-network/Record bound has no completed independent proof review. | current paper correctness section and exact-small preregistration | Correctness certificate | It may appear only as a proposed lemma with a kill condition. | independent derivation required |
| General PEPS hardness does not imply hardness or resource failure of the selected bounded fixture. | admitted Schuch note and project audit | Efficiency/no-go | Do not use worst-case complexity as a numerical resource estimate. | preserve limitation |
| Existing FOCUS and SDIM commit statements are not accompanied by durable local assets sufficient for the current mechanical audit. | prior propagation audit | Candidate catalogue and phase backend | Conjunctive gates depending on those assets remain blocked. | acquire/pin or remove dependency |
| Harper arXiv:2605.29514v1 was present in `CURRENT_CORPUS.toml` as `source_only_reviewed`, but no durable independent-review report supports the named reviewer field. | note metadata, manifest, and repository review-file inventory, checked 2026-07-27 | Adjacent GCAMPS-in-QEC precedent | The scientific content must be treated as draft evidence until a fresh reviewer rereads the pinned PDF and signs a durable report. | admission withdrawn; fresh independent review required |

## Local retrieval log

Backend: artifact-verified local RAG/KG; date: 2026-07-27.

Corpus state at query time: 36 validated notes, 126 concept nodes, 126 edges,
zero dangling edges. A valid corpus does not imply coverage of the ten
unclosed sources above.

Exact RAG queries, each with `--top-k 12`:

1. `Clifford augmented PEPS stabilizer tableau residual PEPS`
2. `measurement reset Born branch mass multi-round syndrome Record tensor network`
3. `CAPEPS full PEPS efficiency bond runtime peak memory`
4. `two-qubit Clifford quotient qutrit 90 disentangler`
5. `PEPS conditional state fidelity Record total variation finite bond error`

The queries returned admitted MPS-hybrid, PEPS-background, instrument-component,
and tensor-network limitation sources. They did not close the direct CAPEPS,
complete Record, finite-bond-to-Record, qutrit, or efficiency rows.

## External acquisition ledger

External search has not yet been executed in this reopen packet. No novelty,
absence, or search-exhaustion claim is permitted.

| gap row | backend + domain / subdomain | exact query + date | candidate + publication status / version | disposition |
|---|---|---|---|---|
| all open rows | pending | pending | pending | `missing`; continue closure |

## Current closure verdict

- `closure_status: open`
- Closed rows: MPS hybrid algebra; general selective-measurement primitive;
  cited reset/XZZX components; admitted qubit Clifford classification facts;
  exact finite-network fidelity objective; PEPS background and general
  worst-case contraction boundary.
- Remaining gaps: direct CAPEPS precedent; complete CAPEPS raw/Record law;
  qutrit catalogue/phase lift; double-sided quotient attribution; Qian
  objective attribution; finite-bond/approximate-contraction to Record error;
  stabilizer-tensor-network and multi-qutrit alternative scopes; matched
  efficiency estimand and result; durable FOCUS/SDIM assets.
- Load-bearing note repair: eleven source-only notes and separate audit packets
  remain required.
- Supported implementation path: retain only the already admitted,
  untruncated qubit algebra/mechanics as bounded engineering evidence.
- Allowed downstream action: acquire and deep-read the named sources, perform
  independent source-only review, rebuild retrieval, and complete external
  disconfirmation search. Do not run stress tests, revise a passing
  preregistration, execute target experiments, or implement target code.
