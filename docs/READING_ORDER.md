# Reading order — what matters at the current stage

Reconciled 2026-07-26 against `0f0c024` plus an uncommitted working tree.
Verify with `python tools/check_reading_order.py`.

`CLAUDE.md` holds the rules that always bind and a routing table for which surface owns which
question. Those are static. **This file holds the part that changes**: what is worth reading right
now, what is in flight, and what has been superseded so you do not read it. If a statement here
conflicts with `docs/SIMULATOR.md`, `docs/SIMULATOR.md` wins.

Keep it short. A long reading list is not read, which is the failure this file exists to fix.

## Current stage

Producing a product that can run a real code, on a one-month clock, accepted as **uncertified**.
Mutation testing is retired; verification is unit tests plus the coverage gate.

## Read first, in this order

1. **`docs/simulator_validation/EXTERNAL_LANDSCAPE_AUDIT_2026-07-26.md`** — re-cuts the scope. A
   multi-round Record for a real surface-code patch under declared non-Pauli noise is not a
   distinguishing deliverable; `stim` supplies geometry, schedule and detector fold at any distance,
   and the nearest published work is listed with locators. Read before writing any scope, novelty,
   or completion sentence. Its differentiator rows carry per-row status and several have already
   narrowed on contact with the literature.
2. **`docs/simulator_validation/2002.07119-claim-audit.md`** — kills a project claim and closes a
   standing modelling gap. Varbanov et al. state the leaked-inert single-qubit gate assumption
   verbatim, and report leakage driving neighbouring defect probability to ~0.5 by reducing the
   affected check to an effective weight-3 anti-commuting check. Companion source-only note:
   `docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md` (deliberately not
   admitted — no renderer, no independent reviewer).
3. **`docs/simulator_validation/HANDOFF_MUTATION_SCOPE_AND_BASELINE_LEGS_2026-07-25.md`** — open
   items 2 through 7 are still open. Item 1 is discharged; its follow-on was deliberately reverted
   rather than fixed, because the mutation layer is being retired.
4. **`docs/service_status.json`**, the `restricted_axis1_1d_mps` note and `excluded_surfaces` — the
   claim boundary. It answers most scope questions outright.

## In flight — uncommitted, decided but not landed

- **Transversal-echo frame repair**, `src/error_coupling_simulator/carrier/within_cycle.py`. The emitted observable carried a
  deterministic `(R-1)*w mod 2` echo sign on top of the logical-flip bit and was inverted at even
  round counts. The parity is derived from the emitted ops and cross-checked by measuring the frame
  on the noiseless codestate, refusing a non-deterministic frame — the construction the exact
  density-matrix leg already used. Reproducers: `scripts/within_cycle_echo_parity_check.py`,
  `scripts/within_cycle_echo_trajectory_frame_probe.py`.
- **Known residual**: the correction is exact only on a leakage-free reference. Under leakage the
  frame is trajectory-dependent, and the deviation is entirely leakage-conditioned
  (`Y^dag Z Y = -Z + 2|2><2|`). That residual is declared noise reaching the record, not a
  bookkeeping error — but it is unbounded, and the two legs share the leaked-inert convention by
  design so they cannot referee each other on it.
- **Corpus manifest rebuilt**: retrievable notes went from 15 to 25 with
  `scripts/rebuild_current_corpus_manifest.py`.

## Superseded — do not act on these

- The mutation-gate scope work and its adjudication issues under `.scratch/mutation-gate-adjudication/`.
  Issue 04 is `wontfix`; the fix was written, validated, and reverted.
- Any claim that the transversal echo converting leakage occupancy into detector signal is novel.
  Withdrawn: prior art in arXiv:2002.07119 and arXiv:1905.12731, and a possible unobservability
  argument recorded in the claim audit.
- Any statement that "no external precedent exists" derived from local retrieval alone. Local
  absence is not a gap; see the rule in `CLAUDE.md`.

## Open decisions

- Whether to commit the in-flight working tree.
- Whether the narrowed echo-parity claim survives the ~0.5 randomization argument. Deciding it needs
  Appendix D of arXiv:2002.07119 and a look at its Fig. 3e — neither possible without a PDF renderer.
- What replaces the retired mutation layer in the release evidence order.

## Unread material already acquired

`docs/papers/1905.12731v1.pdf` and `docs/papers/2607.17204v1.pdf` are retained but read only to
abstract depth. Newly cloned under `external/reference_repos/`: `quantumsim` (the simulator behind
arXiv:2002.07119), `qutrits`, `restless-simulator`, `surface-code-simulator`,
`Located-decoder-for-Rydberg-decay`.

## Maintenance

Update this file when the stage changes, when a read-first entry stops mattering, or when something
lands. Its value is that it is short and current; adding to it without removing is how it dies.
