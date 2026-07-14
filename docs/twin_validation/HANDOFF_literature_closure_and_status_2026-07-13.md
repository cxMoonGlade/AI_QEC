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

## Frozen audit snapshot and scope correction

- Audited base HEAD: `4a226b7914612766723a874651952b763ef3c925`.
- The audit ran this repository-wide mixed regression command:

  ```text
  conda run -n aiqec python -m pytest -q tests/
  ```

- Historical result: `2560 passed, 169 skipped, 9 failed, 56 warnings`; pytest then ended with
  segmentation fault / exit 139. This aggregate was never a simulator-only acceptance suite.
- Eight failures were the `qutip 5.3.0` plus repo-local
  `qutip-cuquantum 0.3.0.dev6+cedd225` read-only-`QobjEvo._dims` compatibility cluster. The canonical
  `ecs` environment now uses qutip-cuQuantum 0.3.1 and the targeted backend slices pass; see
  `CLAUDE.md` for the current commands and counts.
- The remaining `KL=8.15893408390167e-08 > 1e-08` result came from the retired HARDEN-H2
  `RepCodeTwin`/`CoupledRepCodeTwin` calibration study. It is a legacy learner regression, not a
  carrier, noise-process, emitted-record, or simulator-faithfulness gate. The active test tree no
  longer carries that learner suite; no tolerance change was made.
- The historical post-summary native crash occurred in the former mixed execution topology.
  CUDA-Q is now outside canonical `ecs` and runs in its own process; the old aggregate is not
  evidence that the separated canonical topology still exits 139. No new aggregate scientific
  claim is inferred from the targeted environment checks.
- RAG was force-rebuilt over 246 reading notes into 2399 chunks. RAG/KG remain discovery
  surfaces, never evidence.
- Final consistency checks passed: `git diff --check`, Markdown local links, Markdown table
  columns, `docs/code_status.json` parsing, and `tools/gen_code_map.py --check`.

## P0 contract repairs and remaining findings

The 2026-07-13 P0 repair closed three active record/certification defects without changing a
scientific tolerance:

1. `DMOracleAnchor` now fails closed for `R>=2` FULL_JOINT and SYNDROME_DIST requests because
   `QutritDM.record_oracle` supplies moments, not a joint law, there. Direct unsupported calls
   raise a stable contract error before process/DM access; capability cache keys now include the
   requested geometry.
2. `carrier.records.PackedShotBatch` preserves the PEPS raw packed byte layout but applies the
   independently pinned temporal XOR fold at `.to_det_obs()` / `.to_record_batch()`.
   `.to_raw_syndrome_obs()` is explicit. Stim results, Axis-1 sample evidence, and PEPS output now
   share the package-local `RecordBatch` detector/observable boundary.
3. The canonical Stim frontend no longer gates record production on optional PyMatching.
   `Simulator.run(...)`, `run_noiseless(...)`, and `simulate_noiseless(...)` default to
   `decoder=None`; they emit the actual detector/observable records and mark prediction/decoder
   artifacts as `decoder_not_requested`. `decoder="pymatching"` preserves the explicit `[hw]`
   reduction path. Record-only runs retain un-decomposed DEM hyperedges; only that explicit decoder
   path requests graphlike decomposition. The focused Stim/frontend CPU regression is
   `89 passed, 12 skipped` in canonical `ecs` (all skips are explicit `[hw]` decoder tests) and
   `101 passed` in `aiqec` with PyMatching present.
   The broader P0 record/certification/interop contract batch is `156 passed, 6 skipped` in `ecs`
   and `162 passed` in `aiqec`; its six core-environment skips are also optional decoder cases.

Remaining findings:

4. `coupled_cycle` uses a whole-horizon source mean for every round's readout/reset policy,
   so it is not yet a demonstrated causal, prefix-consistent map family.
5. Current source lowering modulates only `zeta` and `gamma_phi`; it does not instantiate the
   previously narrated ten-field source-to-qutrit leakage chain.
6. `exp(L/4)` is a project normalization/siting convention, not a literature-derived physical
   quarter-CZ pulse model.

## Large-distance statement that must remain bounded

Behrends--Beri support numerical plus phenomenological exponential suppression of
**syndrome-conditioned logical-channel coherence** with distance for their independent X-only
channel whenever the incoherent component is nonzero. Bravyi et al. report finite-size washout
under independent product rotations and explicitly leave the asymptotic conversion conjectural.
Neither result is a physical qutrit-leakage-tail, multi-round-record, or PEPS-truncation theorem.

## Next-session task boundary

Continue with the remaining simulator boundary, not new d5/d7 runs and not FET tuning:

1. close and ratify a causal, prefix-consistent per-round instrument object contract before changing
   the source-conditioned implementation; the existing whole-horizon policy remains explicit;
2. keep the two disconnected production-bridge charters `CODE_BLOCKED` until their literature and
   object contracts close.

The common output contract is now present, but a universal backend execution facade is not:
`Simulator.run(...)` remains Stim-representable, while Axis-1 and PEPS retain bounded runners.

Use the `diagnose` workflow. Diagnosis is read-only by default. Any future edit under `src/**`
requires a fresh explicit scope confirmation; literature/object gates remain binding before
claim-bearing experiment code.

## Git/worktree preservation

Preserve all existing environment-lock and setup changes in the worktree. Inspect `git status`
before every edit; do not reset or replace unrelated changes.
