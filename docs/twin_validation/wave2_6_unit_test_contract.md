# Wave-2.6 — Per-Unit Unit-Test Contract (design doc, not code)

Binding parent: `docs/twin_validation/api_hardening_ownership_design.md`
(rows A1/A2/A3, the NAMING STANDARD, the DEVIOUS-TEST STANDARD + K-catalog, the
TWO-SIDED PER-UNIT EXTENSION Side A/Side B). This document is the **per-unit
contract** for **"Wave-2.6: complete per-unit unit tests"**.

## 0. Why this wave exists (the measured gap)

The current Wave-2 gates are **gate-level equivalence + sampled mutation** — they
prove the facade *equals a hand ritual* and that a *sampled* mutant trips a gate.
They are NOT complete **isolated per-unit** tests: whole exception surfaces are
never entered. Coverage proves it.

**Measured coverage** (`.coverage` regenerated 2026-07-07 from
`tests/test_shotset_records.py` + `tests/test_frontend_experiments.py` +
`tests/test_gate_soundness_matrix.py` + `tests/_support/test_support_selftest.py`,
run under the `aiqec` env; `python -m coverage report --include=... --show-missing`):

| Source module | Stmts | Miss | Branch | BrPart | Cover | In-scope missing (this wave) |
|---|---|---|---|---|---|---|
| `error_coupling_simulator/frontend/experiments.py` | 84 | 9 | 38 | 10 | **84%** | 110, 166→169, 200, 208, 211, 214, 217, 220, 223, 330 |
| `qec_twin/forward/scalable/sv_sampler.py` | 545 | 124 | 162 | 37 | 73% | (in-scope units only — see §4) |
| `qec_twin/forward/scalable/mps_forward.py` | 536 | 169 | 180 | 40 | 65% | 465, 493–569*, 660→665 (*mostly out-of-scope; see §5) |
| `tests/_support/fixtures.py` | 89 | 12 | 36 | 6 | **86%** | 37–38, 185, 189, 210, 213, 217, 221, 240–243 |

The `experiments.py` 84% headline is the wave's motivating number: **every one of
the missing lines 200/208/211/214/217/220/223 is a distinct `ExperimentPreset`
`__post_init__` validation raise** — the "7 ExperimentPreset validation raises
untested" the wave brief names — plus line 110 (the empty-env `ValueError`), line
330 (the `leak_slice_table` `TypeError` on a wrong-type arg), and branch 166→169
(the `with_interior_streams=False` leg of `load_xzzx_d3`). None are exotic; they
are the classic "validator never fired" (K-1) surface that gate-level equivalence
tests structurally cannot reach because they only ever pass **valid** inputs.

**Line→unit→partition map** (grounding the exception rows below in measured gaps,
not guesses):

- `experiments.py:110` → `_dataset_files` EXCEPTION: SET-but-empty `QEC_TWIN_D3_DATA` `ValueError`.
- `experiments.py:166→169` → `load_xzzx_d3` BOUNDARY: `with_interior_streams=False` branch.
- `experiments.py:200` → `ExperimentPreset` EXCEPTION: empty `name`.
- `experiments.py:208` → `ExperimentPreset` EXCEPTION: `theta_rad < 0`.
- `experiments.py:211` → `ExperimentPreset` EXCEPTION: `wg_l1_target` out of `(0, 0.5)`.
- `experiments.py:214` → `ExperimentPreset` EXCEPTION: `g_seep`/`g_heat < 0`.
- `experiments.py:217` → `ExperimentPreset` EXCEPTION: `b_bias` out of `[0, 1]`.
- `experiments.py:220` → `ExperimentPreset` EXCEPTION: `arm` not in `SV_ARMS`.
- `experiments.py:223` → `ExperimentPreset` EXCEPTION: `readout_conv` not in `SV_READOUT_CONVENTIONS`.
- `experiments.py:330` → `leak_slice_table` EXCEPTION: neither preset nor RunSpec → `TypeError`.
- `mps_forward.py:465` → `attach_layout` EXCEPTION: non-permutation `order` `ValueError`.
- `mps_forward.py:660→665` → `_leak_sample` BOUNDARY: tie-break FALLBACK leg (`sel = K-1`, no `k` satisfies `target <= cum`).
- `fixtures.py:37–38` → `import torch` except-branch (torch-less box; NAMED CPU exemption, §6).
- `fixtures.py:185/189/210/213/217/221` → builder EXCEPTION rows (numpy-device reject; torch-missing; internal trace/herm asserts).
- `fixtures.py:240–243` → `load_outputs_module` happy path + missing-file precondition.

(The `experiments.py` 84 statements vs 123 physical lines is docstrings; coverage
counts logical statements — the mapping above uses the report's line numbers
directly.)

## 1. K-catalog (reference — every partition below names the classes it defends)

From the parent contract §"The K-catalog": K-1 inert seam / dead parameter · K-2
misindexing (off-by-one, negative-index wraparound, reversed order) · K-3
tie-break/comparison drift (`<=` vs `<`, first-vs-last) · K-4 evil-marginal
thresholds · K-5 self-comparison vacuity · K-6 symmetry blindness (permutation
operators / Mapping-vs-sequence) · K-7 degenerate-input shadowing (NaN, zero-norm)
· K-8 convention/gauge drift (MSB/site-order/units) · K-9 cross-shot/batch
contamination · K-10 measurement-isolation contamination.

## 2. Scope — every public unit added/extended in Wave 2 + 2.5

Enumerated exactly (no more, no less):

**A1 `frontend/experiments.py`** — `load_xzzx_d3`; `ExperimentPreset`
(`__post_init__` + each field); `PRESET_LEAK_THETA_0P30` /
`PRESET_LEAK_WG_L1_5E3` (registered-value pins); `resolve_theta`;
`run_spec_from_preset`; `leak_slice_table` (preset arm **and** RunSpec arm);
`_dataset_files` (module-internal, load-bearing).

**A2 `forward/scalable/sv_sampler.py`** — ONLY the new `ShotSet` methods:
`to_det_obs`, `packed_bytes`, `syndrome_prefix_bytes` (+ their private helpers
`_require_shots`, `_header_geometry` exercised through them). The rest of the
545-line file is OUT of scope (the `cptp_residual` docstring change carries no new
behavior).

**A3 `forward/scalable/mps_forward.py`** — ONLY: `_leak_sample`'s **returned
branch index** (value contract, not the trajectory body); `attach_layout`;
module-level `mps_from_statevector`. The rest of the 536-line file is OUT of scope.

**Test infra `tests/_support/fixtures.py`** — `require_precondition`,
`assert_control_trips`, `assert_with_margin`, `random_cptp_kraus`,
`random_density_matrix`, `load_outputs_module` (+ internal `_assert_cptp`). These
GATE everything else, so they get the most complete coverage; their meta-tests
live in `tests/_support/test_support_selftest.py`.

---

## 3. A1 — `frontend/experiments.py` units

### 3.1 `_dataset_files(dataset_root)` — module-internal, load-bearing

1. **Signature + contract.** `_dataset_files(str|Path|None) -> dict[str, Path]`.
   Resolves the four shipped `d3_at_q6_7` files by root precedence `dataset_root`
   arg > `QEC_TWIN_D3_DATA` env (SET) > parser default (env ABSENT). Rebases the
   parser's `default_*_paths()` via `relative_to(DEFAULT_DATASET_ROOT)`; existence-
   checks every file; raises naming the offender — **never a silent fallback**.
2. **Partitions.**
   - *Normal:* arg=None + env-absent → four default paths (requires_data). arg=real
     root → same four under that root. env=real root, arg=None → resolves under env.
   - *Boundary:* arg wins over a bogus env (precedence, K-3); env-absent vs
     env-present-but-real; override root that replicates layout but omits ONE file
     (the partial-root leg — already exercised at the facade, re-asserted here at
     unit granularity).
   - *Exception (each raise, read from source):* **(a)** env SET but empty/whitespace
     → `ValueError` naming the env var (line 110). **(b)** override root not a
     directory → `FileNotFoundError` naming the root (line 128). **(c)** root is a
     dir but a required file missing → `FileNotFoundError` listing missing (line 138).
3. **KILLERs.** K-1 (dead `dataset_root` param — a silent default fallback must fail
   the bogus-root raise); K-5 (the raise must NAME the offending path under the
   RESOLVED root, so it is provably about OUR root, not an unrelated failure). The
   empty-env `ValueError` KILLER: `QEC_TWIN_D3_DATA=""` must raise, not fall back.
4. **Coverage target.** Statement + branch **100%** for `_dataset_files`. Line 110
   and both `FileNotFoundError` branches (128/138) are CPU-reachable with `tmp_path`
   + `monkeypatch` — no dataset on disk needed for the raise legs (only the happy
   default-resolution leg needs `requires_data`).
5. **CPU/GPU.** CPU-only for all raise legs. `requires_data` ONLY for the
   default-root happy path.

### 3.2 `load_xzzx_d3(dataset_root=None, *, with_interior_streams=True)`

1. **Contract.** Parse r01 geometry (`verify=True`) and — when
   `with_interior_streams=True` — attach r10 interior streams. Root resolution
   delegates to `_dataset_files`.
2. **Partitions.**
   - *Normal:* default streams-attached parse (requires_data; already gated by
     `test_load_xzzx_d3_equals_hand_ritual` — KEPT as integration, re-asserted at
     unit granularity for the branch).
   - *Boundary:* `with_interior_streams=False` — the **166→169 uncovered branch**:
     assert the returned schedule has geometry but NO interior streams attached
     (`len(within_cycle_streams) == 0` or the streams-absent shape).
   - *Exception:* propagates `_dataset_files` raises (covered there; assert one
     propagates unchanged).
3. **KILLERs.** K-1 (a facade returning geometry-only when streams were requested);
   the FALSE branch KILLER (streams-attached vs streams-absent must be
   DISTINGUISHABLE — a facade that always attaches would fail the
   `with_interior_streams=False` leg).
4. **Coverage target.** Statement + branch **100%** (both legs of the
   `with_interior_streams` `if`). requires_data.
5. **CPU/GPU.** CPU-only compute; `requires_data` (needs the shipped patch on disk).

### 3.3 `ExperimentPreset` + `__post_init__` — the 7 field validations

1. **Contract.** Frozen kw-only dataclass; exactly ONE of
   `theta_rad`/`wg_l1_target` set; all physics knobs REQUIRED (no silent defaults).
2. **Partitions.** One VALID representative (raw-angle + wg-rate). Then **one
   EXCEPTION row per raise** (each maps to a measured missing line):

   | # | Trigger | Raise | Line | K-class |
   |---|---|---|---|---|
   | E1 | `name=""` (empty) | `ValueError` "non-empty" | 200 | K-1 |
   | E2 | both `theta_rad` AND `wg_l1_target` set | `ValueError` "exactly ONE" | 201–206 (covered) | K-8 |
   | E2' | NEITHER set | `ValueError` "exactly ONE" | (same branch) | K-1 |
   | E3 | `theta_rad = -0.1` | `ValueError` ">= 0" | 208 | K-1 |
   | E4 | `wg_l1_target = 0.0` and `= 0.5` and `= 0.6` (boundary triples) | `ValueError` "(0, 0.5)" | 211 | K-4 (open-interval edges) |
   | E5 | `g_seep = -1e-9` (and `g_heat = -1e-9`) | `ValueError` ">= 0" | 214 | K-1 |
   | E6 | `b_bias = -0.01` and `= 1.01` (both sides) | `ValueError` "[0, 1]" | 217 | K-4 (closed-interval edges) |
   | E7 | `arm = "Z"` (not in `SV_ARMS`) | `ValueError` "one of" | 220 | K-8 |
   | E8 | `readout_conv = "raw"` (not in `SV_READOUT_CONVENTIONS`) | `ValueError` "one of" | 223 | K-8 |

   BOUNDARY sub-partitions inside E4/E6 are the off-by-one edges of THIS unit:
   `wg_l1_target` uses **strict** `0.0 < x < 0.5` (so `0.0` and `0.5` must BOTH
   raise; `1e-9` and `0.4999` must pass); `b_bias` uses **closed** `0.0 <= x <= 1.0`
   (so `0.0` and `1.0` must PASS; `-eps` and `1+eps` must raise). Frozen-instance
   assignment (`preset.theta_rad = 0.99`) → `FrozenInstanceError` (already at 305–306).
3. **KILLERs.** K-1 (a validator that never fires — every raise DEMONSTRATED via a
   sabotaged field, the `assert_control_trips` shape); K-4 (the interval-edge cases
   distinguish strict-vs-closed — a `<=` drift on `wg_l1_target` or a `<` drift on
   `b_bias` is caught by the boundary triples, NOT by a mid-interval value); K-8
   (`arm`/`readout_conv` enum membership; upper-casing of `arm` via `.upper()` — feed
   `"a"` lower-case as a PASS case to pin the normalization).
4. **Coverage target.** Statement + branch **100%** of `__post_init__` (all 8
   validation branches, both edges of each interval).
5. **CPU/GPU.** CPU-only (pure dataclass validation; no torch, no dataset).

### 3.4 `PRESET_LEAK_THETA_0P30` / `PRESET_LEAK_WG_L1_5E3` — registered-value pins

1. **Contract.** Module-level frozen instances; each knob pinned by REGISTRATION.
2. **Partitions.** Normal only (they are constants). Pin EVERY field:
   `PRESET_LEAK_THETA_0P30` = (theta_rad=0.30, wg_l1_target=None, g_seep=0.09,
   g_heat=0.0, b_bias=0.9, arm="A", readout_conv="biased_b");
   `PRESET_LEAK_WG_L1_5E3` = (wg_l1_target=5.0e-3, theta_rad=None, same other knobs).
3. **KILLERs.** K-8 (knob drift — a silent edit to any pinned value fails). This is a
   REGRESSION PIN, not a logic test: exact `==` on every field.
4. **Coverage target.** N/A (module-level construction is covered by import); the
   assertion is a **value pin** with 100% field coverage.
5. **CPU/GPU.** CPU-only.

### 3.5 `resolve_theta(preset)`

1. **Contract.** Raw-angle preset → returns pinned `theta_rad`; wg-rate preset →
   returns `calibrate_theta_for_wg_l1(wg_l1_target, g_seep=, g_heat=)`.
2. **Partitions.**
   - *Normal:* raw preset → exact float identity with `theta_rad`.
   - *Normal:* wg preset → equals `calibrate_theta_for_wg_l1` at the preset's
     g_seep/g_heat AND independently hits `wg_rates(theta)[0] == target` (already at
     the facade; re-asserted at unit granularity).
   - *Boundary:* both branches of the `if preset.theta_rad is not None`.
3. **KILLERs.** K-1 (a dead wg-resolve passthrough — the resolved theta must differ
   from the raw cell and be > 0); K-8 (RAW theta passes through with NO unit munging).
4. **Coverage target.** Statement + branch **100%** (both convention branches).
5. **CPU/GPU.** CPU-only compute; the wg branch needs the `calibrate_theta_for_wg_l1`
   import (CPU, no GPU, no dataset).

### 3.6 `run_spec_from_preset(preset, *, n_shots, n_rounds, seed, m=0, dataset_root=None)`

1. **Contract.** Build a `RunSpec` from a preset + explicit run-shape kwargs; theta
   via `resolve_theta`; circuit/meta = resolved r01 paths; dtype pinned `"c128"`.
2. **Partitions.**
   - *Normal:* raw preset with distinct run-shape (N=3,R=2,seed=17,m=1) →
     passthrough of all four + physics knobs (requires_data — resolves paths).
   - *Normal:* wg preset → theta calibrated here.
   - *Boundary:* `m=0` default vs `m=1` explicit; `dataset_root` arg forwarded to
     `_dataset_files`.
   - *Exception:* propagates `_dataset_files` raises (bogus root) and
     `RunSpec.__post_init__` raises (e.g. would surface if a preset knob were
     out-of-range — but preset already validates, so this is defense-in-depth).
3. **KILLERs.** K-1 (dead run-shape plumbing — every kwarg DIFFERS from RunSpec
   defaults AND from each other so a swap is caught); K-8 (RAW theta exact identity).
4. **Coverage target.** Statement **100%**; branch 100% except the `dataset_root`
   raise legs which are covered in `_dataset_files` (assert one propagates).
5. **CPU/GPU.** `requires_data` (resolves r01 paths). CPU-only compute.

### 3.7 `leak_slice_table(preset_or_params, *, device, as_list=False)` — BOTH arms

1. **Contract.** Route through `SvSampler.build_within_cycle_leak` (C1-asserted:
   CPTP residual + composition identity embedded, never bypassed). Accept an
   `ExperimentPreset` (theta via `resolve_theta`; sentinel circuit path, no dataset)
   OR a `RunSpec` (passed straight). Return stacked `(n_kraus, 3, 3)` or list form.
2. **Partitions.**
   - *Normal:* preset arm (stacked) — equals the RunSpec arm from the same preset
     (both route to the same builder). RunSpec arm (stacked). `as_list=True` on both.
   - *Boundary:* `as_list` True vs False (the return-shape branch).
   - *Exception:* `preset_or_params` neither `ExperimentPreset` nor `RunSpec` (e.g.
     a dict or `None`) → `TypeError` (line **330**, currently uncovered).
3. **KILLERs.** K-1 (the ExperimentPreset arm was previously dead — the preset arm
   must build from `(g_seep, g_heat)=(0.09, 0.0)`, so a `g_seep<->g_heat` swap gives
   a DIFFERENT table and fails exact `torch.equal`; requires `g_seep != g_heat`
   precondition); K-5 (self-comparison vacuity — the table must CHANGE across cells,
   so a distinct hi-cell table must differ).
4. **Coverage target.** Statement + branch **100%** of the routing +
   `TypeError` + `as_list` branches. The `TypeError` branch (330) is **CPU-only** —
   a wrong-type arg raises BEFORE any GPU work (the `isinstance` chain runs first).
   The two builder-invoking arms are GPU-gated (see below).
5. **CPU/GPU.** **SPLIT unit.** The `TypeError` branch: **CPU-only** (raises before
   `SvSampler(device=)`). The stacked/list builder arms: **`requires_cuda`** — the
   C1 `build_within_cycle_leak` is GPU-hosted (SvSampler contract, "GPU-only
   compute"). NAMED EXEMPTION: the CPTP/composition-assert interior of the builder is
   covered by the existing `requires_cuda` gate `test_leak_slice_table_matches_sv_sampler`
   (KEPT) — the unit test asserts the ROUTING + return-shape, not re-derives the
   builder's asserts.

---

## 4. A2 — `ShotSet` record accessors (`sv_sampler.py`)

All three consume the header + the materialized packed buffer and are **CPU-only**
(numpy pack/unpack — no CUDA, no dataset). A shared fixture builds a synthetic
`ShotSet` from a known `(N, n_stab, R)` syndrome+flip array via
`SvSampler.pack_shots` (the inverse of the accessors), so the reference is
constructed independently of the accessor under test.

### 4.1 `ShotSet.to_det_obs() -> {"det": (N, R*n_stab) uint8, "obs": (N,) uint8}`

1. **Contract.** Unpack via `SvSampler.unpack_shots`, round-major det layout
   (`det[i, r*n_stab + s]`), `n_stab`/`R` from `self.header`. Raise if `shots is
   None` (ValueError) or header lacks `n_stab`/`R` (KeyError). `obs` = sampled flip.
2. **Partitions.**
   - *Normal:* a seeded ShotSet round-trips: `to_det_obs` equals the hand
     unpack+reshape (round-major pinned).
   - *Boundary:* single shot (N=1); `R=1` (one round); the trailing flip byte NEVER
     appears in `det` (it is `obs`).
   - *Exception:* `shots=None` → `ValueError` (via `_require_shots`); header missing
     `n_stab` and/or `R` → `KeyError` naming the missing keys (via `_header_geometry`).
3. **KILLERs.** K-2 (misindexing — a TRANSPOSED layout `det[i, s*R + r]` must fail;
   this is the "AM-3 transpose KILLER self-caught TWICE" bug class — use an
   ASYMMETRIC `(n_stab != R)` geometry so transpose is detectable); K-5 (the round-
   trip is not vacuous — the reference is built by `pack_shots`, the inverse, not by
   `to_det_obs` itself); K-8 (round-major vs stab-major convention, LSB-first).
4. **Coverage target.** Statement + branch **100%** (both `_require_shots` and
   `_header_geometry` raise legs, entered via this method).
5. **CPU/GPU.** CPU-only.

### 4.2 `ShotSet.packed_bytes() -> bytes`

1. **Contract.** `np.ascontiguousarray(shots).tobytes()` — the canonical
   byte-compare surface. Raise if `shots is None`.
2. **Partitions.**
   - *Normal:* equals `np.ascontiguousarray(ss.shots).tobytes()`.
   - *Boundary:* a NON-contiguous `shots` view (e.g. a sliced/strided array) must
     still produce the contiguous bytes (the `ascontiguousarray` is load-bearing);
     single shot; empty is N/A (RunSpec requires N>=1).
   - *Exception:* `shots=None` → `ValueError` (via `_require_shots("packed_bytes")`).
3. **KILLERs.** K-9 (cross-shot contamination — feed a strided/transposed view whose
   `.tobytes()` WITHOUT `ascontiguousarray` would differ; the method must return the
   C-contiguous bytes); K-1 (the None-guard must fire).
4. **Coverage target.** Statement + branch **100%**.
5. **CPU/GPU.** CPU-only.

### 4.3 `ShotSet.syndrome_prefix_bytes(n_rounds) -> bytes`

1. **Contract.** First `n_rounds` rounds' syndrome bits of every shot, packed
   LSB-first, shot-order concatenated, NEVER the flip byte. Requires
   `0 <= n_rounds <= R`. Byte-aligned round boundary → raw per-shot byte slice;
   mid-byte boundary → unpack + truncate-at-round-boundary + repack.
2. **Partitions** — enumerate the ACTUAL edges for THIS unit:
   - *n_rounds = 0* → returns `b""` (the `prefix_bits == 0` early return, line 513).
   - *n_rounds = 1* → one round of bits.
   - *n_rounds = R* → all syndrome bits, but NEVER the trailing flip byte
     (the explicit contract boundary).
   - *n_rounds = R + 1* → `ValueError` (line 509, the `not 0 <= n_rounds <= R` raise).
   - *n_rounds = -1* → same `ValueError` (lower edge).
   - *BYTE-ALIGNED boundary* (`n_rounds * n_stab % 8 == 0`) → the raw byte-slice
     branch (line 517). E.g. `n_stab=8, n_rounds=1` (8 bits = 1 byte) or `n_stab=4,
     n_rounds=2`. Assert it EQUALS the unpack+repack result (the two branches must
     agree on the byte-aligned case).
   - *MID-BYTE boundary* (`n_rounds * n_stab % 8 != 0`) → the unpack+repack branch
     (lines 518–520). **Requires a synthetic `n_stab=3` geometry** (the shipped d3
     `n_stab=8` is ALWAYS byte-aligned, so the mid-byte branch is unreachable on real
     data — this is why the existing gate builds a synthetic `n_stab=3` ShotSet).
     E.g. `n_stab=3, n_rounds=1` → 3 bits, mid-byte; assert the final byte's tail
     bits are zero and round-1's bits do NOT leak in.
   - *Exception:* `shots=None` → `ValueError` (via `_require_shots`); header missing
     `n_stab`/`R` → `KeyError`.
3. **KILLERs.** K-2 (raw byte slicing on a mid-byte boundary LEAKS round-`n_rounds`'s
   bits sharing the boundary byte — the mid-byte KILLER: a raw-slice mutant must
   produce DIFFERENT bytes than the correct unpack+repack); K-5 (the byte-aligned and
   mid-byte branches must be shown to AGREE where both are valid); K-8 (LSB-first
   bit-order — an MSB-first repack scrambles).
4. **Coverage target.** Statement + branch **100%** (the `prefix_bits==0`,
   byte-aligned, and mid-byte branches + the range raise, all CPU-reachable via
   synthetic ShotSets of `n_stab ∈ {3, 8}`).
5. **CPU/GPU.** CPU-only.

---

## 5. A3 — `mps_forward.py` seam units

### 5.1 `_leak_sample(...)` — RETURNED branch index (value contract only)

1. **Contract.** Returns the selected Kraus branch index `sel` (int). Tie-break
   registry (binding, cited verbatim from `batched_mps_backend_prereg.md` v2/v5):
   `sel` = FIRST `k` with `u * tot <= cumsum_k` (**NON-STRICT `<=`**), FALLBACK
   `K - 1` when float accumulation leaves no `k`.
2. **Partitions** — value contract, NOT the trajectory body:
   - *Normal:* a `u` that selects an INTERIOR branch (e.g. `u` in the second
     branch's probability mass) → `sel` equals the analytically-expected index.
   - *Boundary:* `u = 0.0` → `sel = 0` (first branch, `target = 0 <= cum_0`).
   - *Boundary:* `u` just below 1.0 → last branch.
   - *Boundary — the FALLBACK leg* (**660→665 uncovered branch**): `u = 1.0` (or
     `1.0 - eps` where float accumulation of `cum` falls just short of `tot`) → the
     loop finds no `k`, and `sel` retains its initializer `len(pk) - 1 = K - 1`.
     This is the K-3 tie-break FALLBACK — currently never entered at unit level.
   - *Boundary:* the NON-STRICT `<=` edge — a `u * tot` landing EXACTLY on a cumsum
     boundary selects the EARLIER branch (`<=`, not `<`).
3. **KILLERs.** K-3 (tie-break drift — a `<` mutant selects a DIFFERENT branch on the
   exact-boundary `u`; the fallback mutant `sel = 0` instead of `K-1` fails the
   `u=1.0` leg); K-6 (do NOT use a symmetric Kraus set where all `p_k` are equal — a
   permutation-symmetric set hides leg-order bugs; use ASYMMETRIC branch masses so
   the returned index is uniquely determined by `u`).
4. **Coverage target.** The RETURN-VALUE contract of `_leak_sample`: the
   selection-loop branches (interior, first, fallback) + the `<=` edge → **100% of
   the loop + fallback branches** (lines 660→665). NAMED EXEMPTION: the `mps.gate_` /
   `_renormalize` application (lines 665–666) is the trajectory BODY, out of scope
   for the value contract; it is covered by the A3 integration gate
   `test_am5_leak_sample_tiebreak_registry` (KEPT). **This unit needs a real quimb
   MPS + `local_expectation_canonical`, so it is `requires_cuda` in practice** unless
   a tiny CPU-quimb MPS + a monkeypatched/stubbed `local_expectation_canonical`
   returning fixed `pk` is used to isolate the pure selection logic.
   **RECOMMENDED (isolates the value contract, keeps it CPU-only):** refactor the
   test to drive the selection loop with an injected `pk` vector (stub the local
   expectation) — the selection/fallback logic is pure Python arithmetic on `pk` and
   `u`, no GPU needed. If that stub is judged too invasive, the fallback leg stays a
   `requires_cuda` unit (NAMED exemption: fallback branch covered by the GPU gate).
5. **CPU/GPU.** Pure selection logic is **CPU-computable** if `pk` is injected;
   otherwise `requires_cuda` (real MPS local expectation). See OPEN QUESTIONS.

### 5.2 `attach_layout(order, logical_support)`

1. **Contract.** Bind `_mps_order` (site→engine tuple), `_eng_to_mps` (its inverse
   dict), `_log_eng_support`. `order` must be a SEQUENCE permutation of
   `0..len-1`; a `Mapping` is REJECTED (`TypeError`) because dict iteration yields
   keys only (K-6 silent insertion-order reinterpretation).
2. **Partitions.**
   - *Normal:* identity `order = (0,1,2)` → `_eng_to_mps == {0:0,1:1,2:2}`.
   - *Normal:* NON-identity `order = (2,0,1)` → `_eng_to_mps == {2:0, 0:1, 1:2}`
     (the docstring's worked example — pins the INVERSE direction).
   - *Boundary:* single-site `order = (0,)`; `logical_support` empty list `[]` vs a
     populated list.
   - *Exception:* `order` is a `Mapping` (pass `{0:0,1:1,2:2}`) → `TypeError`
     (line 459). `order` not a permutation (`(0,0,1)` duplicate; `(0,1,3)` gap) →
     `ValueError` (line **465**, currently uncovered).
3. **KILLERs.** K-6 (the Mapping rejection — a dict that IS a valid total map would
   pass the permutation check while silently reinterpreting key insertion order;
   the `TypeError` must fire BEFORE the permutation check); K-2 (the INVERSE
   direction — `_eng_to_mps` must be the inverse of `order`, not `order` itself; the
   non-identity `(2,0,1)` example is the discriminator — an implementation that sets
   `_eng_to_mps = dict(enumerate(order))` fails); K-8 (site→engine vs engine→site
   convention).
4. **Coverage target.** Statement + branch **100%** (the Mapping `TypeError`, the
   permutation `ValueError`, and the happy binding).
5. **CPU/GPU.** **CPU-only** (pure dict/tuple construction; no quimb call — this is
   the map-binding half of `sample`, extracted for direct referee use). Construction
   of the `MpsLeakageForward` instance imports quimb (its `__init__` does), so the
   test needs `quimb` importable but NOT cuda; gate with
   `pytest.importorskip("quimb.tensor")` (matching the existing module), NOT
   `requires_cuda`.

### 5.3 `mps_from_statevector(psi, order, device)` — module-level

1. **Contract.** Build a site-ordered qutrit MPS from a dense `3^n` ENGINE-basis
   state vector (site-0-MSB `from_dense(dims=[3]*n)`); the dense tensor is transposed
   into site order so MPS site `k` carries engine axis `order[k]` BEFORE
   factorization. `from_dense` is EXACT (zero-truncation lift, the C8 anchor).
2. **Partitions.**
   - *Normal:* a small `n=2` or `n=3` random normalized `psi` → the MPS
     contracts back (`to_dense`) to `psi` up to the site permutation (round-trip).
   - *Boundary:* identity `order` (no permutation) vs a non-identity `order` (the
     transpose is load-bearing — a non-identity order must reorder axes); `n=1`
     (single site, trivial MPS).
   - *Exception:* none in this unit's own body (delegates to quimb; a mismatched
     `len(order)` vs `psi` size surfaces from `reshape`/`permute` — assert it raises
     rather than silently mis-shaping, if cheaply reachable).
3. **KILLERs.** K-8 (site-0-MSB convention — a row-major-vs-column-major or
   MSB/LSB flip corrupts the round-trip; the "AM-3 transpose KILLER" bug class);
   K-1 (the `order` permutation must be APPLIED — a non-identity order that is
   ignored fails the round-trip against the permuted reference).
4. **Coverage target.** Statement **100%** for `mps_from_statevector`. The device
   argument is exercised on whatever device the test runs (CPU quimb MPS is fine for
   the round-trip — `from_dense` + `as_tensor` is device-agnostic).
5. **CPU/GPU.** **CPU-computable** (quimb `from_dense` on a tiny vector runs on CPU;
   `device` can be `"cpu"` for the round-trip). Needs `quimb` importable
   (`importorskip`), NOT cuda. NAMED note: the production path uses `device="cuda"`,
   but the CONVENTION contract (site-0-MSB round-trip) is device-independent and the
   CPU round-trip is the faithful unit test.

---

## 6. Test infra — `tests/_support/fixtures.py`

These gate everything else → **most complete coverage** (target 100% minus the
one NAMED CPU exemption below). Meta-tests live in
`tests/_support/test_support_selftest.py` (the DEVIOUS-TEST STANDARD: "test
infrastructure defends itself").

### 6.1 `require_precondition(cond, msg, remedy)`

- **Contract.** `cond` false → `AssertionError` prefixed `PRECONDITION (class c, not
  a gate miss): `. Normal: `cond=True` returns None. Exception: `cond=False` raises
  with the EXACT greppable prefix + msg + remedy.
- **KILLERs.** K-1 (a no-op precondition — the raise must fire); the prefix is
  machine-greppable so the meta-test asserts `PRECONDITION_PREFIX in str(exc)`.
- **Coverage.** 100% (both branches). CPU-only.

### 6.2 `assert_control_trips(check_fn, broken_input, gate_tol)`

- **Contract.** Asserts `check_fn(broken_input, gate_tol)` RAISES `AssertionError`
  (the control is live). If it returns normally → this helper raises "CONTROL INERT".
  Non-AssertionError exceptions PROPAGATE (a crashing harness is a bug).
- **Partitions.** Normal: a `check_fn` that DOES raise on the broken input →
  `assert_control_trips` returns None. Exception: **(a)** a `check_fn` that does NOT
  raise → `assert_control_trips` itself raises "CONTROL INERT (vacuous check)"
  (the double-negative KILLER — line ~89). **(b)** a `check_fn` raising a
  `ValueError` (not AssertionError) → propagates unchanged (assert it is NOT swallowed).
- **KILLERs.** K-1 / K-5 (this IS the anti-vacuous machinery; the meta-test must show
  it FAILS when the control does not trip — the parent contract's "shown to FAIL when
  the control does NOT trip" requirement); K-7 (a non-AssertionError must propagate,
  not be miscounted as a tripped control).
- **Coverage.** 100% (tripped, inert, propagate branches). CPU-only.

### 6.3 `assert_with_margin(value, threshold, *, mode, min_margin=10.0, what)`

- **Contract.** Three outcomes: wide pass → returns margin factor; violation →
  plain `AssertionError` (no prefix); knife-edge pass (margin < min_margin) →
  `AssertionError` with `EVIL-MARGINAL (class c): ` prefix. NaN on either side NEVER
  passes (K-7). Non-positive denominator under a passing value → infinite margin.
- **Partitions** — every branch (measured missing lines 185/189 are the mode-error
  and NaN legs):
  - *Normal:* `mode="le"`, `value` well below `threshold` (margin >= 10) → returns
    the factor. `mode="ge"`, `value` well above → returns factor.
  - *Boundary:* margin EXACTLY at `min_margin` (passes — `>=`); margin just below
    (`9.99x`) → EVIL-MARGINAL raise (the K-4 knife-edge, the 1.181e-12-vs-1e-12
    lesson); `value <= 0` under `mode="le"` → infinite margin (documented
    permissiveness); `threshold <= 0` under `mode="ge"` → infinite margin.
  - *Exception:* `mode` not in `("le","ge")` → `ValueError` (line 120). `value` NaN
    or `threshold` NaN → `AssertionError` "NaN never passes" (lines ~123–125, K-7).
    Violation (`value > threshold` for `le`) → plain `AssertionError` (no prefix),
    greppably DISTINCT from the marginal case.
- **KILLERs.** K-4 (the knife-edge — a margin of `9.99` must be reported EVIL-MARGINAL,
  not a pass; a mutant that drops the `min_margin` check passes the knife-edge input);
  K-7 (NaN shadowing — `value=nan` must FAIL, not silently pass a `nan <= t`
  comparison which is `False` but could be mis-handled); the two prefixes
  (`EVIL-MARGINAL` vs none) must be GREPPABLY DISTINCT (a violation must NOT carry the
  marginal prefix).
- **Coverage.** 100% (mode-error, NaN, pass-wide, pass-marginal, violation, inf-margin
  branches — 6 legs). CPU-only.

### 6.4 `random_cptp_kraus(n_kraus, dim, rng, *, backend, stacked, device, dtype)`

- **Contract.** Random CPTP Kraus via QR of a stacked Gaussian block (`Q^H Q = I` ⇒
  `sum_k K_k^H K_k = I`), CPTP-asserted internally at 1e-12 (`_assert_cptp`).
- **Partitions.**
  - *Normal:* `backend="numpy"`, stacked `[n,dim,dim]` → CPTP holds (re-verify
    externally, independent of the internal assert). `backend="torch"`, stacked →
    complex128 tensor. `stacked=False` → list of `dim` matrices (numpy AND torch).
  - *Boundary:* `n_kraus=1, dim=2` (minimum via `require_precondition`); the returned
    `_assert_cptp` residual is well below 1e-12 (route through `assert_with_margin`).
  - *Exception:* `n_kraus < 1` or `dim < 2` → `require_precondition` fires (line ~175).
    `backend="numpy"` with `device`/`dtype` set → `ValueError` "takes no device/dtype"
    (line 185, measured miss). `backend="torch"` with torch=None → `RuntimeError`
    (line 189, measured miss — only reachable on a torch-less box; see exemption).
    unknown `backend` → `ValueError` (line 192).
- **KILLERs.** K-5 (the internal `_assert_cptp` must be shown to TRIP on a sabotaged
  stack — the meta-test's job); K-4 (the CPTP residual margin — a knife-edge near
  1e-12 is EVIL-MARGINAL); the `numpy+device` reject (185) and `unknown backend`
  (192) are dead-parameter KILLERs (K-1).
- **Coverage.** 100% of the CPU-reachable branches. **NAMED EXEMPTION:** line 189
  (`torch is None` → RuntimeError) is UNREACHABLE when torch is installed (it always
  is on the target box). Covered by inspection + the numpy-backend path; a
  monkeypatch of the module-level `torch` to `None` CAN reach it (RECOMMENDED — a
  cheap CPU meta-test that sets `fixtures.torch = None` and asserts the RuntimeError,
  restoring it after). If monkeypatching module state is judged out of bounds, line
  189 is a NAMED exemption (torch-less-box guard, unreachable in CI). Same reasoning
  for line 221 in `random_density_matrix`.
- **CPU/GPU.** CPU-only (numpy backend + torch on CPU device; no cuda needed — the QR
  and CPTP check run on CPU; `device=None` default).

### 6.5 `random_density_matrix(dim, rng, *, backend, device, dtype)`

- **Contract.** `rho = A A^H / tr` (PSD, unit-trace + hermiticity asserted at 1e-12).
- **Partitions.** Normal: numpy → PSD unit-trace hermitian (re-verify externally).
  torch → complex128. Boundary: `dim=2` minimum. Exception: `dim < 2` →
  `require_precondition` (line 203); `backend="numpy"` + device/dtype → `ValueError`
  (line 217, measured miss); torch=None → RuntimeError (line 221, exemption as 6.4);
  unknown backend → `ValueError` (line 223). Internal trace/herm asserts (lines
  209–214, measured miss) — shown to TRIP on a sabotaged rho in the meta-test.
- **KILLERs.** K-5 (internal trace/herm asserts shown to trip); K-1 (numpy+device
  reject; unknown backend).
- **Coverage.** 100% of CPU-reachable branches; line 221 NAMED exemption as in 6.4.
- **CPU/GPU.** CPU-only.

### 6.6 `load_outputs_module(relpath)`

- **Contract.** Import a committed `outputs/` script by relpath-from-repo-root
  (`spec_from_file_location`); must be `__main__`-guarded (import runs no side
  effects). Missing file → loud class-(c) precondition.
- **Partitions.** Normal: a real `__main__`-guarded outputs script imports without
  side effects (lines 240–243, measured miss — the happy path is untested).
  Exception: a nonexistent relpath → `require_precondition` fires naming the path.
- **KILLERs.** K-1 (the missing-file precondition must fire); a side-effect KILLER —
  the imported module must NOT have run its `__main__` body (assert a sentinel the
  script would set only under `__main__` is absent). Use `skip_audit.py` itself (a
  known `__main__`-guarded committed script) as the import target — it is guaranteed
  present and guarded.
- **Coverage.** 100% (import-success + missing-file branches). CPU-only.

---

## 7. Deliverable specification

### 7.1 File layout — one test module per source module

Adopt the straightforward mapping (the wave brief's default):

| Test module | Covers |
|---|---|
| `tests/test_experiments_units.py` | §3 (all A1 units incl. `_dataset_files`) |
| `tests/test_shotset_units.py` | §4 (A2 `ShotSet` accessors) |
| `tests/test_mps_seams_units.py` | §5 (A3 `_leak_sample` value contract, `attach_layout`, `mps_from_statevector`) |
| `tests/_support/test_fixtures_units.py` | §6 — but see note |

**Note on §6:** `tests/_support/test_support_selftest.py` ALREADY exists and is the
registered home for fixtures meta-tests (the DEVIOUS-TEST STANDARD names it
explicitly). The Wave-2.6 fixtures units should **extend `test_support_selftest.py`
in place** (adding the untested partitions — `assert_with_margin` mode-error/NaN,
`load_outputs_module` happy path, the numpy+device rejects, the internal-assert
trips) rather than creating a parallel `test_fixtures_units.py`. RECOMMENDED:
keep `test_support_selftest.py` as the single fixtures test home; do NOT split.
(Confirm in review — this is an OPEN QUESTION only if the wave wants a clean
per-module naming symmetry.)

Naming convention for tests: `test_<unit>_<partition>` (e.g.
`test_experiment_preset_b_bias_upper_edge_raises`,
`test_syndrome_prefix_bytes_midbyte_no_leak`,
`test_leak_sample_fallback_last_branch`). Each test docstring names the K-classes
it defends and, for exception rows, the source LINE it covers (grounding the
statement→partition map above).

### 7.2 Coverage GATE proposal — a committed script (skip_audit shape)

Model exactly on `outputs/twin_validation/skip_audit.py` +
`outputs/twin_validation/skip_audit_run.sh` (the proven gate pattern: printed
evidence header with script + input sha256, a registered JSON, exit 1 on
violation, scripted-execution discipline).

**`outputs/twin_validation/wave2_6_coverage_audit.py`** (proposed):
- Runs (or ingests) `coverage json` restricted to the Wave-2 unit set (the four
  source modules) — the runner `wave2_6_coverage_audit_run.sh` invokes
  `python -m coverage run` over `{test_experiments_units, test_shotset_units,
  test_mps_seams_units, test_support_selftest}` then `coverage json -o <path>`.
- Reads a **per-unit branch-coverage target** from a registered JSON
  `tests/_support/wave2_6_coverage_targets.json` (the exemption registry, see below).
- For each registered unit, computes the unit's statement + branch coverage from the
  coverage JSON's per-file `missing_lines` / `missing_branches`, intersected with the
  unit's line RANGE (start/end lines pinned in the registry — the same source-line
  grounding as §0).
- FAILS (exit 1) if any unit's branch coverage `< target` after removing the unit's
  NAMED exempt lines; prints `UNIT-UNDER-TARGET (VIOLATION): <unit> branch=<x> <
  target=<t>` per failing unit; PASS/FAIL summary line; printed evidence header
  (script sha256 + coverage-json sha256) FIRST.
- Exemptions are DATA in the registry, never inline `# pragma: no cover` scattered in
  src (the parent contract's registration discipline: an exemption is a reviewed diff
  to the JSON, never an auto-refresh).

**`tests/_support/wave2_6_coverage_targets.json`** (proposed shape):
```json
{
  "_comment": ["REGISTERED per-unit coverage targets + NAMED exemptions for",
               "Wave-2.6 (docs/twin_validation/wave2_6_unit_test_contract.md).",
               "A unit below its branch target after removing exempt_lines is an",
               "audit FAILURE. Exemptions are added ONLY by reviewed diff."],
  "default_target": {"statement": 1.0, "branch": 1.0},
  "units": [
    {"module": "src/error_coupling_simulator/frontend/experiments.py",
     "unit": "ExperimentPreset.__post_init__", "lines": [198, 225],
     "target": {"statement": 1.0, "branch": 1.0}, "exempt_lines": []},
    {"module": "src/error_coupling_simulator/frontend/experiments.py",
     "unit": "leak_slice_table", "lines": [289, 337],
     "target": {"statement": 1.0, "branch": 1.0},
     "exempt_lines": [333, 334, 336, 337],
     "exempt_reason": "GPU builder arms (build_within_cycle_leak) covered by the requires_cuda gate test_leak_slice_table_matches_sv_sampler; the CPU TypeError branch (330) is NOT exempt"},
    {"module": "tests/_support/fixtures.py", "unit": "random_cptp_kraus",
     "lines": [162, 192], "target": {"statement": 1.0, "branch": 1.0},
     "exempt_lines": [189],
     "exempt_reason": "torch is None branch: unreachable with torch installed (target box always has it); reached only by monkeypatching fixtures.torch=None, which the meta-test MAY do"}
  ]
}
```
The registry pins each unit's line range (so "unit coverage" is well-defined) + the
NAMED exemptions with reasons. The audit is run per wave gate, alongside the existing
`skip_audit_run.sh`.

### 7.3 Superseded vs kept

**KEPT (as integration gates — additive, not replaced):**
- `tests/test_frontend_experiments.py` — the A1 equivalence gates (facade == hand
  ritual, env-override precedence, leak-table byte-equality). These are
  INTEGRATION gates (facade routing vs a full hand ritual on the real dataset); the
  new `test_experiments_units.py` is ADDITIVE (isolated validation raises + branch
  legs the equivalence gates cannot reach).
- `tests/test_shotset_records.py` — the A2/A3 equivalence gates (`to_det_obs` ==
  hand-roll, mid-byte repack, tie-break registry, attach_layout pure-addition,
  statevector round-trip). KEPT as integration; the unit modules are additive.
- `tests/test_gate_soundness_matrix.py` — the Side-A mutant × gate matrix. KEPT
  (it proves the GATES fail on sabotage; the unit tests prove the UNITS behave on
  isolated partitions — orthogonal).
- `tests/_support/test_support_selftest.py` — KEPT and EXTENDED in place (§7.1 note).

**SUPERSEDED:** none is deleted. The Wave-2.6 units do NOT replace any existing
test — they close the coverage gaps the equivalence gates leave. The one structural
change is EXTENDING `test_support_selftest.py` rather than adding a parallel module.

---

## 8. Summary metrics

- **Unit count:** 19 public/load-bearing units —
  A1 (7): `_dataset_files`, `load_xzzx_d3`, `ExperimentPreset.__post_init__`,
  the two registered presets (as a value-pin unit), `resolve_theta`,
  `run_spec_from_preset`, `leak_slice_table`.
  A2 (3): `to_det_obs`, `packed_bytes`, `syndrome_prefix_bytes`.
  A3 (3): `_leak_sample` (return-value), `attach_layout`, `mps_from_statevector`.
  Infra (6): `require_precondition`, `assert_control_trips`, `assert_with_margin`,
  `random_cptp_kraus`, `random_density_matrix`, `load_outputs_module`.
- **Partition / exception rows (test cases): ~78** — of which **~34 are EXCEPTION
  rows** (every `raise`/precondition in scope): experiments (10: 7 preset fields +
  empty-env + 2 dataset raises + leak-table TypeError), ShotSet (6: 3× None-guard +
  3× KeyError legs), mps seams (4: attach Mapping + non-perm, leak fallback, sv
  round-trip mis-shape), fixtures (14: mode-error, NaN×2, control-inert, propagate,
  numpy+device×2, torch-None×2, unknown-backend×2, internal-assert trips×2,
  missing-file precondition, precondition-prefix). The remaining ~44 are normal +
  boundary rows.
- **Measured-coverage-gap highlights (grounded, from the regenerated `.coverage`):**
  - `experiments.py` **84%** — the 7 `ExperimentPreset` validation raises
    (lines 200/208/211/214/217/220/223) + empty-env `ValueError` (110) + leak-table
    `TypeError` (330) + `with_interior_streams=False` branch (166→169) are ALL
    unhit. This is the wave's headline gap.
  - `fixtures.py` **86%** — `assert_with_margin` NaN/mode-error legs (185/189 region),
    `load_outputs_module` happy path (240–243), the numpy+device rejects
    (210/213/217/221) unhit.
  - `mps_forward.py` in-scope: `attach_layout` non-permutation raise (465) and
    `_leak_sample` tie-break FALLBACK branch (660→665) unhit (the rest of the 65%
    file is OUT of scope — batched op core / trajectory body, D-wave / OPT2-2).
  - `sv_sampler.py` at 73% overall, but the three in-scope `ShotSet` accessors'
    exception legs (None-guard, KeyError) are the targeted gaps; the file's remaining
    miss is the GPU kernel `sample()` path, OUT of scope.
- **Proposed file list:**
  - `tests/test_experiments_units.py` (new)
  - `tests/test_shotset_units.py` (new)
  - `tests/test_mps_seams_units.py` (new)
  - `tests/_support/test_support_selftest.py` (EXTEND in place)
  - `outputs/twin_validation/wave2_6_coverage_audit.py` (new gate)
  - `outputs/twin_validation/wave2_6_coverage_audit_run.sh` (new runner)
  - `tests/_support/wave2_6_coverage_targets.json` (new registered exemption list)

---

## 9. Open questions

1. **Coverage threshold value.** This contract proposes **100% statement + 100%
   branch per in-scope unit** (minus NAMED exemptions). Is 100% branch the wave's
   committed bar, or a slightly-relaxed bar (e.g. 100% statement / ≥95% branch) to
   absorb quimb-internal branches? Recommendation: 100/100 per unit is achievable
   given the exemption registry — but confirm the bar before writing the gate.
2. **`_dataset_files` being module-private.** It is `_`-prefixed but load-bearing
   (all three public A1 entry points route through it). Test it (a) DIRECTLY (import
   the private symbol — fastest path to the empty-env `ValueError` at line 110), or
   (b) ONLY through the public callers (`load_xzzx_d3(dataset_root="")`)? The empty-
   env leg is reachable both ways. Recommendation: test through the public callers
   for the contract, but ONE direct call for line-110 isolation is acceptable
   (private-but-load-bearing units are commonly unit-tested directly here).
3. **`_leak_sample` value contract — stub or GPU?** The pure selection/fallback logic
   (§5.1) is CPU-computable IF `pk` is injected (stub `local_expectation_canonical`).
   Is stubbing a quimb method acceptable to keep this unit CPU-only, or must the
   tie-break registry be exercised on a real GPU MPS (making it `requires_cuda`)?
   The fallback branch (660→665) is the specific gap; a CPU stub reaches it cheaply.
4. **`test_support_selftest.py` extend vs new module.** §7.1 recommends EXTENDING the
   existing selftest module (it is the registered fixtures-meta home) rather than a
   parallel `test_fixtures_units.py`. Confirm — a clean per-module naming symmetry
   would argue for the new module, but it fragments the fixtures meta-tests.
5. **Big-file historical coverage — out of scope for D-wave?** `mps_forward.py` (65%)
   and `sv_sampler.py` (73%) carry large NON-Wave-2 uncovered surfaces (the batched
   op core, the GPU kernel `sample()` path, the trajectory body). This contract
   scopes ONLY the named Wave-2/2.5 units within them. Confirm the historical
   big-file coverage is EXPLICITLY out of scope for D-wave (the coverage gate's line
   ranges enforce this — it never counts out-of-scope lines against a unit's target).
6. **`torch is None` exemption vs monkeypatch.** Lines 189/221 (`backend="torch"` +
   `torch is None`) are unreachable with torch installed. Cover via a `fixtures.torch
   = None` monkeypatch meta-test (reaches the line, restores after), or register as a
   NAMED exemption (torch-less-box guard)? Recommendation: monkeypatch (cheap, CPU,
   reaches the actual line) — but it mutates module state, so confirm it is in bounds.

## 10. Decisions (orchestrator, 2026-07-07 — closing the open questions)

The 6 open questions are resolved as the agent recommended (each has an obvious
correct default); the two genuinely user-facing knobs are flagged for confirmation.

1. **Coverage bar = 100% statement + 100% branch per in-scope unit, minus NAMED
   exemptions** (exemptions are DATA in a registered json, each with a reason + the
   gate that DOES cover it). Rationale: these are small units; a relaxed bar leaves
   the "validator never fired" surface partly dark, contradicting the standard this
   wave exists to enforce. ✅ USER-CONFIRMED 2026-07-07: **100% statement + 100%
   branch** per in-scope unit is the bar, and a STANDING bar for new units going
   forward (named exemptions are the only relief, and each must cite the gate that
   covers the exempted line).
2. **`_dataset_files`:** tested through the public callers for the contract, PLUS one
   direct call for line-110 (empty-env) isolation. Adopted.
3. **`_leak_sample` value contract = CPU, via a stub `mps`** whose
   `local_expectation_canonical` returns a CONSTRUCTED `pk` vector. The unit under
   test is the SELECTION + fallback logic (pure, quimb-independent once `pk` is
   given); stubbing the external read is textbook unit isolation, NOT a toy — the
   physics equivalence stays covered by the GPU AM-5 integration gate. The fallback
   leg (660->665) is reached deterministically by a crafted `pk` where fl-cumsum
   undershoots. Adopted.
4. **Fixtures meta-tests EXTEND `test_support_selftest.py`** (the registered home);
   no parallel `test_fixtures_units.py`. Adopted (do not fragment the meta-tests).
5. **Big-file historical coverage is EXPLICITLY out of scope** (mps_forward 65% /
   sv_sampler 73% non-Wave-2 surface = batched core, GPU `sample()` path, trajectory
   body). The coverage gate enforces this structurally: it scores ONLY the registered
   per-unit line ranges, never counting out-of-scope lines against any target. Adopted.
6. **`torch is None` legs (189/221): monkeypatch** (`fixtures.torch = None` inside a
   restoring `monkeypatch` context) — reaches the real line, CPU, cheap. Adopted;
   the mutation is fixture-scoped and restored.

⚑ USER-FACING #2 (sequencing): RESOLVED 2026-07-07 — land Wave-2 + 2.5 + 2.6 (+ the
L1/L2/L3 layers below) ALL TOGETHER once green; nothing commits until the whole
coverage push is done.

## 11. v2 red-team dispositions (2026-07-07: 2 blockers + 3 amendments, all adopted)

- **BL-1 (leak_slice_table line 335 makes 100% branch unreachable):** the `if as_list:`
  at 335 is reachable ONLY after the GPU `build_within_cycle_leak` call, so no CPU unit
  test enters it, and it was NOT in the exemption list → gate exits 1 forever. FIX: add
  335 to `leak_slice_table`'s `exempt_lines` with the same reason as 336/337
  (GPU-only-reachable; both if-legs covered by the requires_cuda integration gate
  `test_leak_slice_table_matches_sv_sampler`). Symmetric with the already-exempt 336/337.
- **BL-2 (defensive-assert branches are structurally unreachable at 100% — the L1
  necessity proof):** `random_density_matrix`'s inline trace/hermiticity asserts
  (209-214) CANNOT fire for any legitimate input (the construction is Hermitian+PSD+
  unit-trace by algebra), so their raise-side branch is unreachable AND unexempted. This
  is not a one-off — it is the GENERAL shape of a defensive assert (an
  `assert-never-fires` guard against internal bugs). Resolution establishes the standing
  **DEFENSIVE-ASSERT RULE** (§12.1): extract the checks into a module-private
  `_assert_density(rho, tol)` mirroring `_assert_cptp`, so (a) the meta-test trips it
  with a sabotaged rho (the KILLER — proves the assert has teeth) and (b) the unit's L1
  property test proves the LEGITIMATE path never needs it (the invariant always holds).
  The branch is then a registered `defensive_assert` exemption whose reason cites BOTH
  the trip-meta-test and the property-test — never a bare skip.
- **AM-1 (§5.1 fallback description wrong):** the `_leak_sample` fallback leg (660->665)
  is NOT reached by `u=1.0` or `1.0-eps` (both hit the last-k break inside the loop). It
  needs `u` slightly ABOVE 1.0 OR a crafted `pk` whose sequential fl-cumsum undershoots
  `tot` at `u=1.0`. §10.3's "crafted pk where fl-cumsum undershoots" is the correct
  recipe; §5.1's boundary bullet is amended to match.
- **AM-2 (§10.3 stub under-specified):** the CPU stub `mps` must also provide no-op
  `gate_(...)` and `multiply_(...)` (called by `_leak_sample`→`_renormalize` after
  selection), and `kraus` must be long enough that `kraus[sel]` indexes at `sel=K-1`.
  Named so a literal builder does not hit AttributeError.
- **AM-3 (registry under-population games the gate):** `wave2_6_coverage_targets.json`
  MUST enumerate ALL in-scope units with pinned line ranges; an in-scope unit absent
  from the registry is a HARD AUDIT ERROR (not a silent 0-enforcement exemption). The
  audit fails loudly on any enumerated-but-unregistered unit.

## 12. FULL-COVERAGE PROGRAM — L0+L1+L2+L3 over the releasable package (user directive
## 2026-07-07: "能做到更全面的覆盖吗" → L0+L1+L2+L3, scope = the whole
## `error_coupling_simulator` release package)

Structural line/branch coverage (L0) is necessary but NOT sufficient — it proves every
line ran, not that every behavior is correct (a 100%-covered test with weak asserts is
still a mirage). Three more layers make coverage genuinely complete:

### 12.1 L1 — Property-based testing (Hypothesis) + the DEFENSIVE-ASSERT RULE
The project's faithfulness protocol IS a set of invariants; L1 encodes them as
properties and lets Hypothesis generate thousands of inputs + shrink to a minimal
counterexample (the cure for the "hand-picked 'random' input that was secretly the
identity" failure mode). Per-invariant properties (each a Hypothesis test over generated
inputs): CPTP (`sum K^H K = I` for every `random_cptp_kraus` draw), density
(Hermitian+PSD+unit-trace for `random_density_matrix`), byte round-trip
(pack→unpack→pack identity; `to_det_obs` vs the layout transcription), cap monotonicity
(`bond_caps`: `cap_k <= 3·cap_{k-1}` etc.), preset validation (a generated in-range
config constructs; a generated out-of-range value on any field raises), margin
monotonicity (`assert_with_margin`). **DEFENSIVE-ASSERT RULE (standing):** an
`assert-never-fires` guard is covered NOT by structural reachability but by the pair
(extracted `_assert_*` seam tripped in a meta-test with sabotaged input) + (property
test proving the legitimate path preserves the invariant); the structural branch is a
registered `defensive_assert` exemption citing both.

### 12.2 L2 — Mutation testing (mutmut) on CPU-pure modules
`coverage% ran` → `mutation kill-rate` is the objective test-quality metric (it catches
100%-covered-but-weak-assert tests — the automated, exhaustive form of the hand-written
Side-A matrix). Scope: CPU-PURE modules only (numerics, packing, cap arithmetic,
validation, fixtures, closed-form source maths) — GPU/quimb paths are excluded (mutation
runs are too expensive there and their physics is covered by the independent-referee
equivalence gates). Registered target: a per-module kill-rate floor (proposed ≥90%,
survivors triaged — each surviving mutant is either killed by a new test or registered
as an equivalent-mutant exemption with reason). Committed runner + a survivors registry
json, same shape as the coverage/skip audits.

### 12.3 L3 — Scope = the whole releasable package
Extend L0+L1 (and L2 where CPU-pure) from the 19 Wave-2 units to EVERY public unit of
`error_coupling_simulator` (the release package). This needs a unit inventory first (a
read-only sweep enumerating public units per module + classifying CPU-pure vs
GPU/quimb-bound). GPU-bound units keep structural coverage + hand KILLERs + their
existing independent-referee equivalence gates (the faithfulness spine); CPU-pure units
get the full L0+L1+L2 treatment.

### 12.4 Execution program (pilot → package; all lands in ONE final commit set)
- **Stage A (pilot):** the 19 Wave-2 units at L0 + L1 (this validates the coverage gate
  mechanism, the defensive-assert rule, and the Hypothesis harness on a known surface).
- **Stage B:** L2 mutation on the pilot's CPU-pure modules.
- **Stage C (inventory):** enumerate the whole release package's public units (read-only
  agent) → the L3 work-list, CPU-pure vs GPU-bound classified.
- **Stage D:** roll L0+L1 across the package work-list, batch by module; GPU-bound units
  get structural+KILLER+equivalence only.
- **Stage E:** L2 mutation across the package's CPU-pure modules; final coverage +
  mutation + skip audits all green; then the whole Wave-2..2.6 + L1/L2/L3 set is
  presented for ONE commit confirmation.
Each stage: committed runner + audit, full-suite regression, un-led review before any
gate run; nothing commits until Stage E is green.
