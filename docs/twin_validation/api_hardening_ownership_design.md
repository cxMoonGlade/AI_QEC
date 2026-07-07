# API-Hardening Ownership Design (2026-07-07, pre-registration of the refactor contract)

Synthesized from the three inventories against `docs/CODE_MAP.md` (error_coupling_simulator = releasable target, qec_twin.forward.exact/scalable not yet migrated; xzzx_parser slated to move "with frontend/mechanisms phases") and the CLAUDE.md module-placement + faithfulness rules.

## Ownership table

| # | New/owning module | What moves in | Source copies to migrate | Referees + independence constraints | Consumers after migration | Phase | Risk notes |
|---|---|---|---|---|---|---|---|
| A1 | **`src/error_coupling_simulator/frontend/d3_cell.py`** (NEW; home = open decision 1) | The cell facade: `load_d3_schedule(root=env-overridable, with_streams=True)` composing `default_r01_paths`/`default_r10_paths` → `parse_xzzx_circuit(verify=True)` → `parse_within_cycle_streams(r10)` → `with_within_cycle_streams`, with r01-geometry/r10-streams provenance explicit in the return; a **named-cell registry** (`CellSpec`) holding the two theta conventions as distinct registered cells (`RAW_THETA_030` = p2's theta=0.30/g_seep=0.09/b=0.9/arm=A vs `WG_L1_5E3` = `calibrate_theta_for_wg_l1` at same g_seep/b) — NO silent physics defaults, knobs always explicit per registered-sweep rule; `build_leak_table()` returning both stacked `[K,3,3]` and list forms; sched-level `stab_isx()` and `stream_filter(('H','X','LEAK'))` helpers | `tests/test_p2_mps_per_round_leak.py` `_sched_and_spec`/`_spec_at`/`_base_leak`; `tests/test_soft_readout.py` `_physical_problem` + 2 in-file stab_isx/streams copies; `outputs/twin_validation/p1c...py:109-137`, `residual2...py:189-214` sv_spec closure; ~23 teacher_prereg scripts (grep: 76–106 files hit the ritual) | None — declared shared-arm input plumbing (both kernel and DM arms legitimately consume one `WithinCycleMarshalled`; parser is not an arm under test). Constraint: keep the embedded `cptp_residual`/`compose_residual < 1e-12` (a)-class preconditions inside the facade, and keep the two theta conventions as *separate named cells*, never a merged default | All carrier tests, all gate scripts, future OPT2-2 harnesses, product code | **A** | Imports qec_twin.forward.{exact,scalable} cross-package until xzzx_parser/sv_sampler migrate — acceptable (frontend already imports qec_twin.hardware). `DEFAULT_DATASET_ROOT` hard-coded absolute path gains an env override here (open decision 7). New src module ⇒ needs user mainline confirmation |
| A2 | **`src/qec_twin/forward/scalable/sv_sampler.py`** (EXTEND) | `ShotSet.det_obs()` → certify-ready `{'det':(N,R*n_stab) uint8,'obs':(N,)}` (n_stab/R from header, kills hand unpack+reshape); `ShotSet.packed_bytes()` + `ShotSet.syndrome_prefix_bytes()` (syn_bytes arithmetic already in `unpack_shots`); ONE canonical `cptp_residual` entry (re-export/alias the audit one; document the 1e-12-gate vs 1e-8-engineered-precondition tolerance pair as named constants) | p2 `_packed` + its older inline expansion (lines 82-84); soft_readout hand-rolled syn_bytes prefix compare; the 4 cptp_residual routes (`_assert_cptp` hand-roll, SvSampler method, floor_backend, bayes_floor); the unpack→reshape→marginal hand-rolls feeding certify | Byte-identity vs the SAME engine is self-comparison, not certification — no referee status, safe as methods. `cptp_residual` caveat travels in the docstring: **cert usages must not use the arm-under-test's own residual function** (soft_readout deliberately uses floor_backend's) — keep all entry points, document which is cert-grade for which arm | p2, soft_readout, lsoft8, certify `emitted_statistic` callers, interop bridge | **A** | src/qec_twin change ⇒ explicit user confirmation before commit; regression = full suite + packed-buffer byte-identity on an existing seeded sample |
| A3 | **`src/qec_twin/forward/scalable/mps_forward.py`** (EXTEND, minimal API-gap closure) | (1) `_leak_sample` returns its selected branch index (kills the `_cumsel` replica of lines 578-586 and its silent tie-break-drift trap); (2) a public `prime_for_terminal_readout()` seam (kills `_prime_fwd` ritual ×2); (3) `mps_from_dense(vec)` module-level (kills `_qmps_from_dense_row`/`_qmps_product` re-rolls); (4) named convention anchors (e.g. `# CONVENTION: site-0-MSB` tagged blocks) replacing the ~10 raw line-number citations sprinkled across harness helpers | test_batched_mps_ops `_cumsel`/`_prime_fwd`/`_qmps_from_dense_row`; degenerate_guard `_fwd`/`_qmps_product` | The serial arm IS the referee for batched_mps — exposing its selection/loader as API is fine (referee-side); the constraint is on consumers: batched-side harnesses may import these serial helpers, **soft_readout may NOT** (there mps_forward is the arm under test — its `_arm_d2`/`_qutrit_gate_local` copies stay duplicated by design) | OPT2-1/OPT2-2 test suites, degenerate_guard | **A** | src change + tie-break registry (prereg v2/v5: `u*tot <= cumsum_k`, fallback K-1, strict-vs-nonstrict split) must be cited verbatim at the return-value definition. Byte-identity regression on serial `sample()` mandatory. User confirmation required |
| B1 | **`src/error_coupling_simulator/certify/anchors/dm_oracle.py`** (EXTEND — or new `sequential_null.py`, open decision 2) | The **sequential-null two-branch Lüders Φ referee** graduating from p1c (lines 164-204): non-selective per-stab channel via clone-branch1 + alias-death branch0 + in-place recombination (~3.3 DM-copy peak, both stab kinds); `DETECTOR_MARG` gains an explicit `semantics=` parameter (`"isolated"` \| `"sequential"`, **no default — fail-loud**), closing chip **task_e194ccf4**; the P1c-6 iso-vs-seq per-detector gap becomes reportable anchor data | `outputs/twin_validation/p1c_full9q_record_bound.py:164-204` (sole occurrence — promoted because it is a registered chip/finding); the isolated clone-rho1 loop copies (p1c iso arm, residual2 `_detector_marg_probe`, `_probe_r2_full9q_oracle`) collapse onto the existing dm_oracle path | **LOAD-BEARING REFEREE.** Referees: the sampled SV trajectory kernel (`sv_traj_d3_wc`) and MpsLeakageForward records. MUST run on `QutritDM` exact engine only; MUST NOT import or re-derive from `sv_sampler` kernel paths, `mps_forward`, or `batched_mps`. Shared `WithinCycleMarshalled` input stays a *declared* model-matching choice, documented as such. The isolated/sequential distinction must be interface-carried, never collapsed (the D1-critical v2 review finding) | certify_teacher level grids, future P1c-class record gates, residual2-family scripts | **B** | Memory pattern is subtle (alias-death correctness depends on single-remaining-consumer) — port with the v2 review notes as inline comments + the removed all-X false-trip assert documented. Keep the copy-count in the Capability descriptor honest (~3.3 vs 4). Regression: recompute p1c marginals, pin vs committed p1c json at 1e-9 (the P1c-4 pattern) |
| B2 | **`tests/_support/batched_discriminators.py`** (NEW test-support pkg) | OPT2-1-corrected discriminator utilities: `_pick_branches` (ascending-Choi-eigh weight-ranked picking — the FIX-2 lesson), knife-edge margin family (`_margin_ok_cumsum`/`_assert_margin_*`/`_safe_u_*`/`_u_for_branch`), `_assert_sigma_conditioning`, `_low_rank_batch` **with the sigma fence and rank asserts baked INSIDE the builder** (so no copy can omit them; kills the gop5 inline near-copy drift), `_gop3_engineered_case`, `_haar_batch`, both **zero-norm drivers as named variants** (projective `annihilate` vs artificial `zero_gate` — different renormalize paths, keep both), `_cumsel` (until A3 lands, then deleted) | test_batched_mps_ops lines 256-544 + gop5 inline builder 1690-1699; degenerate_guard `_annihilate` | Class-(c) harness machinery, not a referee — but the **prereg tie-break registry** (batched_mps_backend_prereg v2/v5) citations must travel verbatim; brick-wall-unsoundness lesson (operator Schmidt rank 9 not 3) stays in the builder docstring | OPT2-1 gates, the whole OPT2-2 batched-sample() gate suite | **B** | Stays under `tests/` (never src — production must not depend on test randomness conventions). `_cumsel` is deleted the moment A3 ships; sequencing B2 after A3 avoids migrating it at all |
| B3 | **`tests/_support/serial_referee.py`** (NEW) | Serial-arm probe kit: `_fwd` cheap-constructor + priming (folded once A3's public seam lands), `_serial_hard2`/`_serial_hard3` probe-then-drive-real-private-method pattern, dense-row/product-state MPS loaders (folded into A3's `mps_from_dense`) | test_batched_mps_ops `_fwd/_prime_fwd/_serial_hard2/_serial_hard3` (~100 LOC); degenerate_guard merged `_fwd` | Serial side referees batched_mps: **import-ban on `batched_mps`** enforced by a module-top assert/comment. Also the single home where the mps_forward convention citations rot in ONE place. **Must fix the stale FIX-5 docstrings** (test_batched_mps_ops lines 604-614, 1324-1333 still describe the PRE-fix NaN-shadowed serial guard that degenerate_guard now certifies as fixed) — the two files currently assert opposite things | test_batched_mps_ops, degenerate_guard, OPT2-2 | **B** | The FIX-5 comment reconciliation is a correctness-of-record fix, do it in the same commit as the move so the contradiction never migrates |
| B4 | **`tests/_support/sv_mcwf_gt.py`** (NEW, GT-only module) | The from-scratch SV-MCWF trajectory GT (WG-Kraus sample + Born stab measure + √E_s collapse + X/Y echoes + terminal read, ~75 LOC) + `_svb_parity_vec`/`_svb_apply_1q` + the hand-rolled Gaussian/quadrature GT + soft_readout's own `_arm_d2`/`_qutrit_gate_local` copies | test_soft_readout lines 63-232 (single test copy, but a second home in `outputs/twin_validation/` P2-ii (b)/(c) scripts is already declared — cross-home drift of biased_b/echo/drop_postY conventions is the registered risk) | **Strictest constraint in the suite**: shares ONLY inputs (codestate, leak Kraus, parsed geometry); **import-ban on `forward/scalable` (mps_forward, batched_mps) AND QutritDM**; Gaussian helpers use neither scipy nor arm-A's torch grid (third integrator by design). Module docstring points to its own certification script (`d2c_probe_svmcwf_vs_dm.py`) | test_soft_readout, P2-ii record-level gate scripts | **B** | If P2-ii scripts can't import from `tests/` cleanly, mirror via the `load_outputs_module` direction instead (open decision 5). Do NOT merge its `_arm_d2` with the mps_forward import used in test_batched_mps_ops — opposite sharing rules, cleanest independence example in the suite |
| C1 | **`tests/conftest.py`** (NEW) | `_HAS_CUDA`/`_HAS_DATA` probes with ONE `_HAS_DATA` definition (all 4 files: r01 circ+meta AND r10 circ+meta — the strict p2 variant); `requires_cuda`/`requires_data` markers with canonical reasons; `DEVICE/CDTYPE/RDTYPE/PHYS` constants; dataset-root env override plumbed to A1 | 7+ files' preambles (p2, soft_readout, batched_mps, degenerate_guard, seam, qutrit_dm_exact ×its try/except + hardcoded abs path, qutrit_dm_memlean); out-of-scope files opt in later | None — pure environment probing. Constraint: **GPU-only house rule = hard skip, never CPU fallback** — memlean's `cuda if available else cpu` is a divergence to eliminate on migration, not encode | Every GPU/dataset-gated test | **C** | Widening `_HAS_DATA` to the strict 4-file check could newly skip soft_readout/seam on partial datasets — correct behavior, but note it. Leave the `QEC_TWIN_HW_DATA` hardware-test convention alone (separate, documented) |
| C2 | **`tests/_support/fixtures.py`** (NEW) + conftest fixtures | Canonical d3-cell fixture wrapping A1; random CPTP-Kraus/mixed-rho builders (one builder, backend + return-shape flags: numpy/torch, list/stacked, device); `precondition(cond, msg, remedy=...)` emitting the machine-greppable `"PRECONDITION (class c, not a gate miss): ... remedy: re-seed"` prefix; `assert_control_trips(check_fn, broken_input, gate_tol)` micro-helper (assertion SHAPE only); `load_outputs_module(relpath)` importlib shim | `_random_cptp_kraus`/`_rand_cptp_kraus`/`_rand_rho*` (2 in-scope + 4 out-of-scope files); ~15 scattered precondition asserts with drifting vocabulary; qutrit_dm_exact's spec_from_file_location shim (+ its try/finally monkeypatch → pytest fixture) | Random INPUT generation is not a referee — safe to centralize. `assert_control_trips` centralizes the ritual's *shape* only; **the bespoke broken-input controls themselves stay local** (that bespokeness IS the scrutinize-vacuous-checks discipline) | All test files; future gate suites get greppable precondition-vs-gate-miss semantics | **C** | Keep out of src/. Tolerance for controls: default to the real check's gate tolerance, ad-hoc values become explicit args |
| D1 | **`outputs/twin_validation/_run_gate.sh`** (ONE generic runner) | The committed-runner skeleton: `set -u`; **literal $-free PATH export** (wsl.exe pre-expansion trap); `mkdir -p` log dir; optional evidence header mode (`git_head; date -Is; sha256sum <sources...>`); `python`-script vs `python -m pytest -q` mode; `2>&1 \| tee $LOG`; `rc=${PIPESTATUS[0]}; echo python-exit=$rc \| tee -a; exit $rc` — the exit **always propagated** (fixes the residual2/p0 swallowed-exit variant) | ~15 .sh copies (p1a/p1c/residual2/opt2_0/p0/p2ii/opt2_1/run_n3_*/run_notion3_*/run_full_suite; `_p4a_env.sh` stays a separate sourceable env bootstrap) | Plumbing, but it is the scripted-execution audit-trail surface: PIPESTATUS capture inside the inner shell + literal PATH are non-negotiable; the sha256 header mode becomes available to ALL runners (today only the pytest-gate variant has it) | Every future gate run; existing .sh become 2-line wrappers or are regenerated | **D** | outputs/ is gitignored-adjacent — the runner must itself be committed (verify outputs/twin_validation tracking status first). Per-script log names stay explicit args, never derived silently |
| D2 | **`docs/twin_validation/gates/_gate_common.py`** (EXTEND in place; relocation = open decision 3) | Adds the helpers the p1*/opt2*/residual2/notion3 families hand-roll: `script_evidence()` (own-script-bytes sha256 — **the ONE content-hash convention**, open decision 4 — + git_head + GPU assert + version print, printed FIRST); `emit_gate_result` reuse; binomial-SE z gate (`binomial_z(p_hat, null, N)` with the clip-1e-30 guard) alongside the existing bootstrap zscore — **never silently interchangeable** (registered-gate SE convention rule; iid understates clustered records by DE up to ~4×); `BANDS`/`_band` findings-not-crashes checker (residual2's mature form: miss ⇒ FINDING recorded, exit 0; gate-fail exit semantics stay per-script registered); incremental `_dump`; `bench()`/peak-memory/OOM-as-data helper (warmup outside timed region + OOM ⇒ recorded bound, never crash); load-prior-json-and-pin-at-1e-9 reproducibility helper (the P1c-4 pattern) | residual2 `_content_hash/_git_head/_dump/_band`; p1a inline bands; p1c z-gate block; the ~40 GATE_RESULT scripts' preamble ritual (migrate opportunistically, new scripts mandatorily) | `cluster_bootstrap_se` stays the honest-SE referee for clustered records (resamples source clusters, never shots); the binomial z's null MUST come from the independent referee arm — helper docstring carries this. **Predict-before-measure guard: no helper may fill or generate bands — the docstring prereg header stays hand-authored before the run** | All new gate scripts; step2/g6 already consume | **D** | Three incompatible hash conventions exist (script-bytes / payload-json / script+json sidecar) — pick script-bytes as canonical, keep the notion3 sidecar writer as an opt-in function rather than breaking its convention retroactively. sys.path.insert-of-docs import stays until open decision 3 resolves |
| D3 | *(no new module — migration wave)* | Port the 7 in-scope test files + p1a/p1c/residual2/opt2_0/p0 onto A1/A2/A3/B/C; delete the superseded local helpers; reconcile FIX-5 comments (B3) | All rows above | Per-row constraints apply during the port; where a local copy exists BECAUSE of an independence rule (dense-apply referees, soft_readout's `_arm_d2`), the port **adds a one-line "deliberately local, referees X, must not import Y" comment** instead of migrating | — | **D** | Full suite is the net after every wave; byte-identity checks (packed ShotSet buffers, serial sample() output, p1c 1e-9 pin) where applicable |

## Explicitly NOT centralized (stays local, by independence rule)

- **The dense window/site apply referee family** (`_dense_apply_window` et al., 4 copies) — each referees a different arm with a different required blind-spot profile; a single shared dense-apply lib is the exact FAITHFULNESS_PROTOCOL Rule-I failure mode. At most one library **per refereed arm**, and today no arm has ≥2 copies on its own side ⇒ all four stay file-local with the new "deliberately local" comment.
- **soft_readout's `_arm_d2`/`_qutrit_gate_local`** vs test_batched_mps_ops' mps_forward imports — same 3-line function, opposite sharing rules; never merge (they move into B4 vs stay imports respectively, still two copies).
- **Bespoke anti-vacuous broken-input controls** (7 in soft_readout + the enumeration/scramble/monkeypatch controls) — only the assertion *shape* (C2's `assert_control_trips`) and message convention centralize.
- **The prereg-binding docstring header** — stays hand-authored prose per script; no generator (would gut predict-before-measure).
- **Per-script registered constants** (BANDS values, Z_GATE=4, seeds, cell knobs) — helpers accept them, never default them.

## Open decisions

1. **Cell-facade home**: `error_coupling_simulator/frontend/d3_cell.py` (migration-direction-aligned; cross-imports qec_twin until xzzx_parser/sv_sampler move) vs `qec_twin/forward/scalable/cell.py` (zero cross-package imports today, needs a shim later). Recommendation: error_coupling_simulator/frontend — the parser is already slated to land there, and D-phase consumers are simulator-side.
2. **Sequential null: extend `DMOracleAnchor` vs new `SequentialNullAnchor`**. Recommendation: extend dm_oracle with a mandatory-explicit `semantics=` parameter (no default) — keeps the split-semantics visible in one Capability descriptor and closes task_e194ccf4 in the anchor the level grids already route to; a second class would silently let the isolated cell keep its class-(a) band-0 score unquestioned.
3. **`_gate_common` relocation**: stay under `docs/twin_validation/gates/` (extend in place, keep sys.path.insert) vs promote to `error_coupling_simulator/` as an installed module. The docs/ location violates no hard rule but the import mechanism is fragile; promoting it makes gate plumbing "product" — arguably wrong (evaluator/gate tooling, not simulator). Suggest: extend in place now, revisit at the migration's frontend/mechanisms phase.
4. **Canonical content-hash convention**: own-script-bytes (p1* family) recommended; is the notion3 `.json.sha256` sidecar retired for new scripts or kept as opt-in?
5. **`tests/_support/` package vs conftest-only**: outputs/ gate scripts (B4's second home) cannot cleanly import from `tests/` — either B4 lives in `tests/_support/` and scripts re-certify their own copy, or B4 gets an outputs-side home loaded via `load_outputs_module`. Needs a call before B4 lands.
6. **A2/A3 src-mainline changes** need explicit user confirmation (confirm-mainline-before-commit rule) — batch them as one reviewed diff or split per method?
7. **Dataset-root env var name** (e.g. `QEC_TWIN_D3_DATA`) and whether it also serves the spark remote-node path.

## Proposed execution order + gate/regression strategy

1. **Wave 1 — C1 (conftest) + C2**: pure test-side, zero src risk. Gate: full suite green with identical pass/skip counts per file (skip-count diff is the regression signal for the `_HAS_DATA` strictening).
2. **Wave 2 — A2 + A3 (src extensions, one reviewed diff, user confirmation)**: additive API only, no behavior change. Gate: full suite + **byte-identity** of (a) a seeded `sample()` packed buffer before/after, (b) serial `MpsLeakageForward.sample` output (A3's `_leak_sample` return value must be a pure addition). Then A1 (facade) consuming them; gate: p2 + soft_readout ported produce identical assertions/seeds.
3. **Wave 3 — B2/B3 (test support)**: mechanical moves + the FIX-5 stale-comment reconciliation. Gate: test_batched_mps_ops + degenerate_guard green, `_cumsel` deleted (A3 supersedes), grep confirms no batched_mps import in serial_referee/no forward-scalable import in sv_mcwf_gt (add as a tiny import-ban test).
4. **Wave 4 — B1 (sequential-null anchor, the load-bearing one)**: port with review notes; gate: recompute the p1c sequential + isolated marginals through the anchor and **pin vs the committed p1c result json at 1e-9** (P1c-4 pattern); the P1c-6 gap values must reproduce; close chip task_e194ccf4. This is the only wave needing a GPU run — a committed script under outputs/, run by the executor per scripted-execution discipline (not this design pass).
5. **Wave 5 — B4** after open decision 5; gate: soft_readout green + its certification-script pointer verified present.
6. **Wave 6 — D1 + D2**: runner + gate_common extensions; gate: one existing gate script (p1a, findings-semantics) re-run through the new runner reproduces its committed result json values and `python-exit` evidence line.
7. **Wave 7 — D3 migration wave**, file-by-file, full suite after each; scripts migrate opportunistically (new scripts mandatorily), never retro-editing committed result jsons.

Throughout: the full pytest suite (`conda run -n aiqec python -m pytest -q tests/`) is the net after every wave; byte-identity wherever a packed buffer, serial sample, or prior result json exists; no wave builds on an unconfirmed src change.

## Ratified decisions (user, 2026-07-07)

All seven open decisions resolved as recommended: (1) cell facade in `error_coupling_simulator/frontend`;
(2) extend `dm_oracle` with a MANDATORY-explicit `semantics=` parameter (no default); (3) `_gate_common`
extended in place; (4) script-bytes = the canonical content hash, the notion3 sidecar becomes opt-in;
(5) the statevector reference lives under `tests/_support/`, outputs scripts import it via an explicit
sys.path insert (evaluator tooling, not product); (6) A2/A3 land as ONE reviewed diff with one user
confirmation; (7) dataset-root env var = `QEC_TWIN_D3_DATA`.

## NAMING STANDARD (user directive 2026-07-07: "we are building a TOOLKIT" — names must be
## standard-vocabulary and self-explanatory to an external user, not project shorthand)

Principles (binding for every NEW public name in this pass; existing internals rename only when touched):
- **N-1 Glossary consistency.** One public vocabulary across modules/docstrings/docs, aligned with the
  certify seam's already-public terms: *reference* (a from-scratch or independent implementation used
  for comparison — replaces the internal "referee"/"GT"), *anchor* / *control* (the certify ports),
  *preset* (a named, registered experiment configuration — replaces the internal "cell"),
  *backend under test* (replaces "arm") , *gate* (a registered pass/fail check; defined once in the
  test-support README). Internal docs may keep the old shorthand; APIs may not.
- **N-2 No history in names.** Phase/finding codenames (p1c, opt2, gop3, FIX-5) never appear in an API
  name — they live in docstrings ("promoted from the P1-c script"), commit messages, and preregs.
- **N-3 Expandable abbreviations.** Any abbreviation in a public name must be standard (MPS, DEM, CPTP)
  or expanded in the name itself (`statevector_reference`, not `sv_mcwf_gt`; `wood_gambetta_*` spelled
  out at first use in the docstring).
- **N-4 Units/conventions in ambiguous parameter names** (the lambda-vs-sigma lesson): `theta_rad`,
  `gap_lambda`, `ratio_sigma`, `n_rounds` — never a bare `gap`/`ratio`/`R` in NEW public signatures.
- **N-5 Underscore only for genuinely-private.** `tests/_support/` keeps its underscore (pytest
  collection convention); module and function names inside are clean.

Rename table (design-table v1 name -> product name):

| Entry | v1 proposal | Product name | Notes |
|---|---|---|---|
| A1 module | `frontend/d3_cell.py` | **`frontend/experiments.py`** | loads schedules + builds run specs + noise tables |
| A1 loader | `load_d3_schedule` | **`load_xzzx_d3()`** | returns the parsed schedule with interior streams attached |
| A1 registry | `CellSpec` / `RAW_THETA_030` / `WG_L1_5E3` | **`ExperimentPreset`** / `PRESET_LEAK_THETA_0P30` / `PRESET_LEAK_WG_L1_5E3` | presets are frozen + named; no silent defaults |
| A1 leak builder | `build_leak_table` | **`leak_slice_table()`** | returns the stacked `(n_kraus, 3, 3)` table; list form via a flag |
| A2 records | `ShotSet.det_obs()` | **`ShotSet.to_det_obs()`** | matches the registered `{"det","obs"}` payload keys (C-3) |
| A2 bytes | `packed_bytes` / `syndrome_prefix_bytes` | **`packed_bytes()`** / **`syndrome_prefix_bytes(n_rounds)`** | explicit rounds argument (N-4) |
| A3 loader | `mps_from_dense` | **`mps_from_statevector()`** | mirrors the existing `_mps_from_statevector` semantics |
| A3 priming | `prime_for_terminal_readout` | **`attach_layout(order, logical_support)`** | says what it does, not why a test needs it |
| B1 param | `semantics=` | **`measurement_semantics="isolated"\|"sequential"`** | mandatory, no default |
| B2 module | `tests/_support/batched_discriminators.py` | **`tests/_support/state_builders.py`** + **`tests/_support/sampling_guards.py`** | states (Haar/low-rank blocks/engineered spectra) vs guards (knife-edge margins, weight-ranked branch selection, sigma conditioning fence) |
| B3 module | `tests/_support/serial_referee.py` | **`tests/_support/mps_serial_reference.py`** | "reference", names the backend it references |
| B4 module | `tests/_support/sv_mcwf_gt.py` | **`tests/_support/statevector_reference.py`** | N-3 |
| C2 helper | `precondition(...)` | **`require_precondition(cond, msg, remedy=...)`** | greppable prefix unchanged |
| D1 runner | `outputs/twin_validation/_run_gate.sh` | **`outputs/twin_validation/run_gate.sh`** | user-invoked tool, no leading underscore |
| D2 module | `_gate_common.py` | keep filename (existing) | public helpers get clear names (`script_evidence`, `binomial_z(p_hat, p_null, n_shots)`) |

Plus: a short **GLOSSARY section in the test-support README** (reference/anchor/control/preset/gate/
backend-under-test) written in Wave 1 so every later wave names against it.

## v2 REVIEW DISPOSITIONS (un-led adversarial review 2026-07-07: 3 blockers + 8 amendments, ALL adopted)

- **BL-1 (Rule-I referee collapse):** A2's cptp_residual consolidation is RESCINDED as written. The
  contract declares a canonical PAIR: `SvSampler.cptp_residual` (arm-side: the arm's own build/entry
  preconditions) and `floor_backend.cptp_residual` (audit-side: every cert gate, e.g. L-soft-6) remain
  independent implementations FOREVER; only same-side duplicates collapse; each caller's side is
  registered in the docstring. A single shared implementation would let one conjugation bug pass both
  the precondition and the cert gate.
- **BL-2 (runner trackability):** `git check-ignore` confirms nothing under `outputs/` can be tracked.
  The generic runner moves to **`tools/run_gate.sh`** (tracked, beside gen_code_map.py); outputs/
  runners become 2-line wrappers calling it.
- **BL-3 (semantics routing unenforced):** Wave 4 gains the DISCRIMINATING gate: the P1c-6
  false-failing detectors must go GREEN under `measurement_semantics="sequential"` AND still TRIP
  under `"isolated"` at the recorded 4.7-6.6 sigma; every certify grid cell REGISTERS its semantics
  value (no mechanical all-isolated migration).
- AM-1: the semantics value is carried as an EXPLICIT field threaded through the grid/check definition
  (exact mechanism fixed in the Wave-4 mini-design); migration surface = core.py, facade.py,
  tests/test_certify.py.
- AM-2: Wave 1's gate gains a Rule-II falsifying probe — collect the suite with `_R10_META` masked
  (via `QEC_TWIN_D3_DATA` pointing at a partial copy) and assert EXACTLY the intended test set skips;
  memlean's cuda-else-cpu -> hard-skip conversion is DECLARED a behavior change (GPU-only house rule).
- AM-3: one-time gate BEFORE any consumer deletes its hand-roll: `ShotSet.to_det_obs()` equals the
  existing hand-rolled unpack+reshape on a committed seeded ShotSet (round-major layout pinned).
- AM-4: `test_mps_terminal_degenerate_guard.py` is marked ARM-UNDER-TEST for mps_forward — its
  `_qmps_product`/`_fwd` loaders stay "deliberately local" (join the NOT-centralized list); only
  soft_readout-style exemption logic applies.
- AM-5: `_cumsel` deletion is amended — ONE hand-computed tie-break conformance micro-test on the A3
  return value survives (the prereg registry keeps an executable transcription outside the arm).
- AM-6: B1's geometry/streams arrive AS DATA (facade/teacher-supplied WithinCycleMarshalled), never by
  importing sv_sampler from dm_oracle; the Wave-3 import-ban test EXTENDS to B1.
- AM-7 text fixes: Wave 6 is ALSO a GPU wave (p1a asserts CUDA) with the 1e-9 pin convention named;
  `_cumsel` removed from B2's move-in list (dead by sequencing); Wave-3's grep target is
  `statevector_reference` and runs at Wave 5; p2/soft_readout port their CELL-RITUAL parts in Wave 2
  and their remaining support parts in Wave 7; open decisions are all resolved (see Ratified
  decisions) so no deadlines needed.
- AM-8: the tolerance-constant registry carries all THREE conventions: `CPTP_TOL=1e-12` (gate),
  `1e-8` (engineered-violation precondition floor), and floor_backend's documented `1e-9` build
  tolerance (retire the phrase or name the constant — decided at Wave-2 diff time).

## DEVIOUS-TEST STANDARD (user directive 2026-07-07: "要做更阴险的单元测试" — binding for every
## NEW test in this pass and after)

Design question every test must answer BEFORE it is done: **"what is the most devious implementation
that still passes me?"** — then add the discriminator that kills it. Concretely:

- **KILLER requirement.** Every load-bearing assert ships at least one KILLER: a deliberately
  sabotaged input/implementation variant DEMONSTRATED to trip that assert (the
  `assert_control_trips` shape). A check that has never been shown to fail is unproven
  (scrutinize-vacuous-checks discipline, now mandatory per-assert, not per-review).
- **Meta-tests for test infrastructure.** Everything in `tests/_support/` gets its own self-test
  module: `require_precondition` shown to raise with the greppable prefix; `assert_control_trips`
  shown to FAIL when the control does NOT trip (the double-negative killer); `random_cptp_kraus`'s
  internal CPTP assert shown to trip on a sabotaged build. The probe/mask machinery defends itself:
  an UNKNOWN mask name in `QEC_TWIN_D3_MASK` raises loudly (a typo silently masking nothing = a
  vacuous probe).
- **The K-catalog** (every entry is a REAL bug class caught in the 2026-07-06/07 arc; new tests
  check themselves against it and name which classes they defend):
  K-1 inert seam / dead parameter (the P2-ii caller-table-ignored trap) · K-2 misindexing
  (off-by-one, Python negative-index wraparound, reversed order) · K-3 tie-break/comparison drift
  (`<=` vs `<`, first-vs-last, argmax-on-bool) · K-4 evil-marginal thresholds (engineered violation
  landing a hair above the gate: the measured 1.181e-12 vs CPTP_TOL=1e-12) · K-5 self-comparison
  vacuity (identical cap tuples; engine-vs-own-oracle) · K-6 symmetry blindness
  (permutation-symmetric operators hiding leg-order bugs; sign-blind observables) · K-7
  degenerate-input shadowing (NaN-swallowed guards; zero-norm batch poisoning) · K-8
  convention/gauge drift (MSB/site-order/lambda-vs-sigma units) · K-9 cross-shot/batch
  contamination (gather misalignment) · K-10 measurement-isolation contamination (absolute peaks
  counting other tests' standing allocations).
- **Discriminator patterns** (the reusable answers): byte-level positive controls (injection ==
  equivalent static run), prefix-identity checks (round-0 block EXACT equality), sabotage variants
  (swapped enumeration, reversed tables), unit tags in names, masked-environment probes,
  heterogeneous-batch vs B=1 replays.
- Optional lever: automated mutation testing (mutmut-class) on CPU-pure modules (cap arithmetic,
  packing, guards); GPU paths use hand-authored KILLERs.

### TWO-SIDED PER-UNIT EXTENSION (user directive 2026-07-07: "不该通过的报通过, 该通过的报
### 不通过/skip, 逐unit进行测试" — false POSITIVES and false NEGATIVES, unit by unit)

- **Side A — soundness matrix (should-fail-must-fail), PER UNIT:** for every public unit of the
  hardened API surface, a MUTANT × GATE matrix: inject a specific sabotage (monkeypatch the unit —
  e.g. to_det_obs -> transposed layout; _leak_sample tie-break -> strict `<`; syndrome_prefix_bytes
  -> raw byte slice; bond_caps -> off-by-one; leak_by_round -> constant index; preset knob swap) and
  assert the corresponding gate FAILS (AssertionError), parametrized over the whole matrix — not
  spot checks. Home: `tests/test_gate_soundness_matrix.py` (gates callable as plain functions).
- **Side B — liveness / anti-false-alarm (should-pass-must-pass-robustly):**
  (i) MARGIN discipline: tolerance-bearing gate asserts route through `assert_with_margin(value,
  tol, min_margin=10.0)` (tests/_support) — a pass within 10x of its threshold is EVIL-MARGINAL and
  reported/failed as a precondition (the measured 1.181e-12-vs-1e-12 lesson, now structural);
  (ii) preconditions must NEVER fire in the committed suite (they are re-seed guidance for
  development; a firing precondition in CI = a failed gate, visible by the greppable prefix);
  (iii) SKIP ALLOWLIST: the full-suite junitxml skip set must EQUAL the registered allowlist
  (file -> count + reason, `tests/_support/skip_allowlist.json`); ANY unregistered skip = audit
  failure — this closes the hasattr/importorskip escape-hatch class suite-wide, not just in
  reviewed files. Audit home: a committed script parsing the junitxml (run per wave gate).
- Scope now: the Wave-2 units (A1 experiments facade, A2 ShotSet accessors, A3 seams) + the P2-ii
  leak_slices seam. The batched-MPS op core's matrix (22 gates, its own review-verified KILLERs)
  is REGISTERED as an OPT2-2 entry gate rather than duplicated here.