# GCAPEPS/CAPEPS evidence bundle — 2026-07-27

This directory is a copy-only working snapshot. Every pre-existing source
remains at its original repository path; no source file was moved or renamed.

## Current scope override

The binding current target is the narrow GCAMPS-to-GCAPEPS mathematical
feasibility result: exact finite-lattice representation closure and explicit
worst-case PEPS bond bounds. The current entry point is
`01_manuscript/current/GCAPEPS_CURRENT_MANUSCRIPT_POINTER_2026-07-27.md`.

The older CAPEPS/XZZX manuscript, architecture, Record closures,
preregistrations, and comparator material are retained for provenance. They are
not instructions to resume the broader programme, even where their copied path
contains the historical directory name `current`.

The historical snapshot includes the former full rewrite, its 22 academic
references plus one software reference, the CAPEPS target closures, and the transitive
source-note/audit chains required by the included PEPS and Record background
closures. It is not a wholesale mirror of every topic in
`CURRENT_CORPUS.toml`; unrelated current-corpus records remain in their
canonical repository locations.

## Scientific status

Packaging does not change the evidence grade of any item. The current theorem
packet is `MATHEMATICAL_CONTENT_REVIEWED_PASS`; its independent review records
the initial counterexample, repair, and post-repair PASS. The theorem proves
exact finite representability only. It does not prove low bond dimension,
efficient contraction, runtime or memory advantage, Record correctness, or a
complete QEC simulator.

The former CAPEPS Record-efficiency closure (`OPEN_SPLIT_VERDICT`), numerical
preregistration (`NOT_ELIGIBLE`), target implementation (`CODE_BLOCKED`), and
disentangler gate remain historical statuses. They do not gate or widen the
current mathematical note.

## Layout

- `00_CURRENT_GCAPEPS_MATHEMATICAL_PACKET/`: minimal current packet containing
  only the mathematical manuscript/proof/review chain and its four-source
  literature chain.
- `01_manuscript/current/`: current GCAPEPS mathematical note, theorem pointer,
  and architecture, plus two retained broad-draft copies explicitly marked
  historical by the current pointer.
- `01_manuscript/historical_context/`: superseded drafts retained only for
  provenance.
- `02_scientific_closure_and_audits/`: literature closures, source audits,
  preregistrations, baseline results, and artifact-only reviews.
- `03_project_contracts/`: binding simulator, metric, faithfulness,
  provenance, corpus, architecture, service, module, and test contracts.
- `04_reading_notes/current_source_reviewed/`: the 27 direct or transitively
  load-bearing source-reviewed notes, admitted under their own front-matter
  status.
- `04_reading_notes/legacy_context_only/`: legacy notes that must not be used
  as current evidence.
- `05_literature_pdfs/local_cache/`: PDFs copied from the existing repository
  cache.  “Local cache” alone does not mean “admitted evidence.”
- `05_literature_pdfs/cited_downloaded_not_admitted/`: papers cited by the
  manuscript or closure but missing, or missing at the required version, from
  the local cache.  They were downloaded from official arXiv PDF endpoints on
  2026-07-27 and have **not** thereby become source-reviewed or admitted.
- `06_literature_provenance/local_cache/`: existing provenance sidecars.
- `07_literature_text/local_cache/`: existing PDF text extractions retained
  locally but deliberately excluded from the committed payload and root
  manifest because repository-wide policy ignores `*.txt` cache files.
- `MANIFEST.sha256`: integrity manifest for the committed payload, generated
  after assembly. It excludes both manifest files and the local-only
  `07_literature_text/` cache.

## Downloaded-but-not-admitted sources

The load-bearing exact-version files are:

- `quant-ph_0408190v2.pdf`;
- `1210.7011v2.pdf`;
- `1606.06301v2.pdf`;
- `2110.12726v2.pdf`;
- `2602.15942v2.pdf`.

`1811.05497.pdf` follows the closure's unversioned citation.  Four additional
unversioned filename aliases (`quant-ph_0408190.pdf`, `1210.7011.pdf`,
`1606.06301.pdf`, and `2110.12726.pdf`) are byte-identical to their v2 files
and are retained only to record the initial reference-table fetch.

The existing cached `2602.15942v1.pdf` is not a substitute for the v2 source
used by the disentangler closure.  The v2 copy is therefore isolated in the
downloaded-not-admitted directory.

## Non-PDF software reference

Reference [7] in the current manuscript is the `events555/sdim` GitHub
repository at inspected commit
`115c495b23ade35ef0f68b7299afef463129bf51`.  It is a software dependency, not
a literature PDF, so this bundle records the pointer through the manuscript
and CAPEPS module contract rather than copying an external repository.

## Interpretation rule

Directory membership is inventory, not endorsement.  For scientific use,
prefer the chain

`exact source PDF -> source-reviewed note -> audit/closure -> preregistration`.

Any break in that chain is an explicit evidence gap, not permission to infer
the missing step.
