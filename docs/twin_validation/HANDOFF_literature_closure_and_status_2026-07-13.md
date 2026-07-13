# HANDOFF — literature closure and current simulator status (2026-07-13)

> **Purpose:** thin, current resume record. It routes to the audited sources instead of
> duplicating their derivations. `docs/SIMULATOR.md` remains the binding specification;
> `CLAUDE.md` remains the current project router.

## Resume verdict

The project is **not** an end-to-end, record-faithful d5/d7 production simulator. It has a
strong engineering substrate and several locally credible components, but the scientific
production bridge is:

```text
closure_status: open
downstream_gate: CODE_BLOCKED
preregister_claim_allowed: false
```

The source-conditioned dense-qubit path (Charter A) and static data-qutrit XZZX path
(Charter B) are disconnected implementation islands. In the recorded search corpus, the
number of direct published papers closing either complete bridge is zero. This is a corpus
statement, not a theorem that such literature cannot exist.

The only skill-qualified `confirmed-literature-gap` is the narrower bridge from a local TN
truncation score to a bound on the complete record law or rare-event LER. It is not a global
nonexistence theorem.

## Read in this order

1. [`CLAUDE.md`](../../CLAUDE.md) — main line, current gate, live-test status, commands.
2. [`docs/SIMULATOR.md`](../SIMULATOR.md) — binding object and carrier contract.
3. [`production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`](production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md)
   — actual A/B code flows, literature ledger, open rows, live test snapshot.
4. [`coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`](../nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md)
   — coherent-tail and truncation closure.
5. [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md)
   — object taxonomy and no-go boundaries.
6. [`docs/NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md) and
   [`docs/METRICS.md`](../METRICS.md) — value and metric trust ledgers.

## Frozen current-HEAD evidence

- Audited base HEAD: `4a226b7914612766723a874651952b763ef3c925`.
- Full suite command:

  ```text
  conda run -n aiqec python -m pytest -q tests/
  ```

- Live result: `2560 passed, 169 skipped, 9 failed, 56 warnings`; pytest then ended with
  segmentation fault / exit 139.
- Eight failures are one `qutip 5.3.0` plus repo-local
  `qutip-cuquantum 0.3.0.dev6+cedd225` compatibility cluster: the baseline writes the now
  read-only `QobjEvo._dims`. A representative test reproduced independently.
- The ninth failure is independently reproducible:
  `test_h2_phi_parity_and_sign_minima` observed
  `KL=8.15893408390167e-08 > 1e-08` after 342.14 s.
- The post-summary native crash is a separate unresolved stability defect. It has not been
  minimized or proved benign.
- RAG was force-rebuilt over 246 reading notes into 2399 chunks. RAG/KG remain discovery
  surfaces, never evidence.
- Final consistency checks passed: `git diff --check`, Markdown local links, Markdown table
  columns, `docs/code_status.json` parsing, and `tools/gen_code_map.py --check`.

## Active code-contract findings

1. `QutritDM.record_oracle` supplies a full joint only for `R=1`; for `R>=2` it supplies
   moments, while `DMOracleAnchor` can still advertise a feasible FULL_JOINT request and then
   read a missing `joint` field.
2. Legacy `ShotSet.to_det_obs()` labels round-major raw syndrome as `det` without the required
   temporal XOR fold. Any detector-level result must be traced to its exact accessor.
3. `coupled_cycle` uses a whole-horizon source mean for every round's readout/reset policy,
   so it is not yet a demonstrated causal, prefix-consistent map family.
4. Current source lowering modulates only `zeta` and `gamma_phi`; it does not instantiate the
   previously narrated ten-field source-to-qutrit leakage chain.
5. `exp(L/4)` is a project normalization/siting convention, not a literature-derived physical
   quarter-CZ pulse model.

## Large-distance statement that must remain bounded

Behrends--Beri support numerical plus phenomenological exponential suppression of
**syndrome-conditioned logical-channel coherence** with distance for their independent X-only
channel whenever the incoherent component is nonzero. Bravyi et al. report finite-size washout
under independent product rotations and explicitly leave the asymptotic conversion conjectural.
Neither result is a physical qutrit-leakage-tail, multi-round-record, or PEPS-truncation theorem.

## Next-session task boundary

Start with **P0 diagnosis**, not new d5/d7 runs and not FET tuning:

1. minimize the qutip-cuQuantum compatibility failure;
2. diagnose the reproducible H2 KL gate miss without changing its tolerance first;
3. minimize the post-pytest exit-139;
4. then specify fixes for the `R>=2` oracle contract, detector fold, and causal per-round
   instrument policy.

Use the `diagnose` workflow. Diagnosis is read-only by default. Any edit under `src/**` still
requires the user's explicit confirmation; literature/object gates remain binding before
claim-bearing experiment code.

## Git/worktree preservation

The literature/status audit was staged as a documentation checkpoint but was **not committed**
by the save step. Preserve all staged changes, including the user's pre-existing staged
`AGENTS.md` and `.agents/skills/zoom-out/SKILL.md`; do not reset or replace them.
