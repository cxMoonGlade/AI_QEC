# Current GCAPEPS mathematical packet

Date: 2026-07-27

Status: `CURRENT__MATHEMATICAL_FEASIBILITY_REVIEWED_PASS`

This directory is the minimal, copy-only packet for the current project scope:
take the GCAMPS frame--residual representation from
\(C|\mathrm{MPS}\rangle\) to \(C|\mathrm{PEPS}\rangle\), and prove that the
result is mathematically well defined on every finite connected lattice. No
original file was moved.

The proved constructive bound is

\[
D'_e\le rD_e
\]

on edges of a selected routing tree for a pulled-back operator with \(r\)
nonzero Pauli-product terms; unrouted edges are unchanged. A nonidentity qubit
Pauli rotation has \(r\le2\). An adjacent two-site Clifford refactor has the
safe bound \(D'_e\le d^2D_e\).

This is an exact finite-representability theorem, not an efficiency theorem. It
does not establish small bonds, efficient PEPS contraction, runtime or memory
advantage, Record correctness, or a complete QEC simulator.

## Read in this order

1. `manuscript/GCAPEPS_CURRENT_MANUSCRIPT_POINTER_2026-07-27.md`;
2. `proof_and_review/GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`;
3. `proof_and_review/GCAPEPS_MATHEMATICAL_FEASIBILITY_INDEPENDENT_REVIEW_2026-07-27.md`;
4. `manuscript/GCAPEPS_TECHNICAL_NOTE_DRAFT_2026-07-27.md`;
5. `proof_and_review/GCAPEPS_TECHNICAL_NOTE_INDEPENDENT_CONSISTENCY_REVIEW_2026-07-27.md`;
6. `manuscript/GCAPEPS_MATHEMATICAL_ARCHITECTURE_2026-07-27.md`.

After any context compaction, consult
`proof_and_review/CAPEPS_RESEARCH_STATE_CHECKPOINT_2026-07-27.md` rather than
reconstructing the state from chat memory.

## Minimum literature set

Each source has a copied PDF, a source-reviewed reading note, and a source or
project-fit audit under `literature/`.

- arXiv:2511.06672v2 supplies the GCAMPS \(C|\mathrm{MPS}\rangle\) skeleton,
  Clifford frame update, commute-through step, and paired refactor identity.
- arXiv:2605.29514v1 is the direct GCAMPS continuation. It still uses
  \(C|\mathrm{MPS}\rangle\) and lists PEPS/TTN as future layouts; it does not
  supply the GCAPEPS closure theorem.
- arXiv:1405.3259v2 supplies finite-PEPS definitions and algorithmic background.
- Schuch--Wolf--Verstraete--Cirac, PRL 98, 140506, supplies the generic PEPS
  contraction-hardness boundary used only in the limitations.

The tree-routed product-sum PEPO lemma and the per-edge bond bounds are project
derivations, not statements attributed to these papers.

`MANIFEST.sha256` records the integrity of every payload file in this minimal
packet.
