# c64 screening-engine plan for the 2D PEPS carrier (DRAFT, 2026-07-11)

> **Status: CONTINGENT DRAFT.** Build this ONLY if the c128 round-2 triage says "continue"
> AND a multi-round (~20–30 round) bond-saturation run is needed and is too slow / OOM-prone in
> c128. c64 is a **SCREENING accelerator, NOT the evidence engine** — c128 stays the ground-truth
> oracle (the SW-S8 `complex128 ALWAYS` contract). This is a **bounded simplification** under
> `docs/FAITHFULNESS_PROTOCOL.md` rule III: the bound is the frozen-replay validation in §5;
> unbounded = STOP.
>
> Grounded by the `c64-plan-recon` workflow (5 code mappers + 1 adversarial numerical skeptic,
> 2026-07-11) cross-checked against direct reads of `trajectory.py` / `dynamics.py`. Every
> file:line below is from that recon.

---

## 0. The asymmetric trust rule (read this first)

The skeptic's verdict is **MARGINAL, not turnkey**, and the residual risk is **directional**:

- FP32 round-off **accumulation** (~√720·6e-8 ≈ 1.6e-6 over R=30 at 24 stab/round) plus
  NTU-on-noise can bias the eps-rank **DOWNWARD** → a **false "bounded/saturates"** → the
  **UNSAFE** direction (ships a wrong feasibility conclusion).
- Numerical-noise-as-weak-decoherence biases the bond **UPWARD** → a **false "grows"** → the
  **SAFE** direction (only wastes c128 time).

**⇒ THE RULE:** a c64 **"grows / No-Go"** flag may stand as a screening trigger. A c64
**"bounded / saturates / GO"** MUST be confirmed by c128 at the same rounds before it is
reported. Never invert this.

---

## 1. The one structural fact that makes it cheap

`torch.linalg.qr/svd/svdvals` **return the dtype of their input**, and the input is always a
STATE tensor (`t.data`). So **casting the STATE to c64 auto-runs the ~97%-cost boundary-MPS
reads + insertion SVDs + QR in c64 "for free"** — that IS the 10–30× win.

The work is therefore NOT "rewrite the linalg". It is three things:
1. **Thread dtype** so the reconstruction casts inside the cutters don't silently up-cast the
   written-back state back to c128 (which kills the speed AND trips the `__init__` dtype gate).
2. **Make the 1e-12-class thresholds dtype-aware** (they sit 5–6 orders below the c64 ~1e-7
   floor and break — silently or loudly).
3. **Validate** against c128 on a frozen branch (§5).

---

## 2. dtype threading (the plumbing)

There are **three independent `CDTYPE=complex128` globals** plus one hard construction gate:

| Where | What | Action |
|---|---|---|
| `peps/state.py:45-46` | CDTYPE/RDTYPE — imported by contraction, stab_tt, trajectory | thread per-run dtype |
| `pepo/dynamics.py:49-50` | its OWN CDTYPE — the reused cutters | thread (or c64 variant) |
| `pepo/layout.py` (←`exact.qutrit_dm`) | CDTYPE for the codestate build | build c128 → cast |
| `peps/state.py:142-143` | `PepsState.__init__` HARD-asserts `dtype==complex128` (SW-S8) | **the first wall** — parametrize to the state's declared dtype |
| `sv_sampler.py:227,238` | `RunSpec.dtype` exists + validated to {c128,c64} but **IGNORED** by `PepsSampler` (latent bug: header stamps `dtype` while the run is c128, `trajectory.py:746`) | wire it into `PepsSampler.sample` |

**Do NOT mutate the c128 globals in place** — the c128 evidence engine and the c64 screening
engine must coexist. Thread a per-run `dtype` parameter.

Concrete threading points (all from the recon):
- **Codestate:** build once in c128 (cheap), run all sector / `<S>`/`<L>` / **structural
  `|2>`-mass** asserts in c128, THEN `.to(complex64)` the site-tensor network before the
  trajectory loop (mirror `sv_sampler.py:1379-1380`). `state.py:214-299`.
- **Operators stay c128, cast at apply:** `qutrit_gate` (`dtype` param already exists — callers
  at `trajectory.py:554,709`, `state.py:244`, `stab_tt.py:186` just omit it), stab-TT cores
  (`stab_tt.py:190` — add `.to(dtype)` at `_insert_core`), leak Kraus (`trajectory.py:385`),
  terminal/cap/effect ops (`contraction.py:77,334,461-478`), the boundary-fit initial guess
  (`contraction.py:131-134` — the **exact reverse of the already-fixed v4.2 backend-matched-guess
  bug**: a c128 guess against a c64 network re-introduces the mismatch).
- **Cutter reconstruction casts** (`dynamics.py`): `sqrt_s.to(CDTYPE)` (`:686`), `MA/MB` zeros
  (`:777-780`), `Rm` (`:788`), `_gauge_cut_pair` (`:557`) — these must cast to the STATE dtype,
  not the hardwired pepo c128, or every precut/NTU write-back reverts the state to c128.
- **KEEP `RDTYPE=float64` even in the c64 build.** `dynamics.py` already does
  `s_sq=(S*S).to(RDTYPE)` (`:554,683,763`) — the f64 upcast de-noises the eps-tail cumsum for
  free. **Close the asymmetry:** `trajectory.py` `_sq_tail`/`_rank_for_tail` use `(S*S).real`
  which stays f32 (`:165,180`) — cast those to float64 too, so the ~1e-8 tail is accumulated in
  f64 on top of the f32 sigmas.

---

## 3. Tolerance handling (the correctness core)

**Split `NUMERICAL_ZERO`'s dual role** (`numerics.py:3`): it is used both as an O(1) positivity
floor (c64-safe) AND as a *relative* SVD drop threshold `sigma > 1e-12·sigma_1` (c64-broken).
Keep 1e-12 for the floors; introduce a separate **~1e-6 relative** rank/drop threshold for the
c64 SVD paths.

Four tiers:

### (A) NO CHANGE — survives c64 (the screening signal + the safe floors)
- **The load-bearing cut** `_rank_for_tail` at `eps_spike=1e-8` (`trajectory.py:174-191`): cuts at
  σ/σ₀ ~ 1e-4, **~3 orders above** the c64 ~1e-7 floor → the **RANK (the bond-saturation
  observable) is resolvable in c64**, incl. the 1e-10 rider arm (~1e-5, still 2 orders up).
- All **O(1)-norm positivity floors** (`>1e-12` in state/contraction/trajectory) — norms are
  O(1), 1e-12 ≪ c64 noise, never false-trip.
- `p0`/`p1` clamps, `clamp(e, min=0)` before sqrt — these *help* at c64.
- The sampling_maps tie-breaks (`sampling_maps.py` — keep byte-identical; shared with killer tests).
- The §6.1 window-discard invariant (`trajectory.py:242-270`) — tails are ~1e-8 vs a boundary far
  below; defensive branch unreachable below W_max in spec.

### (B) RELAX to ~1e-6 (dtype-aware) — else SILENT wrong-rank / LOUD crash / lost speedup
- **`_exact_rank`** `sigma>1e-12·sigma_0` (`trajectory.py:199`) + the `re` reads in
  `svd_precut_bond`/`ntu_truncate` (`dynamics.py:682,762`) + `gap_rank` floor (`dynamics.py:490`) +
  diagnostics rank probes → **inflate to noise-full → false NON-saturation.** Relax to ~1e-6·σ₀
  **or compute the rank from a c128 spectrum.**
- **stab-TT `_tt_svd` drop** (`stab_tt.py:114`, `dynamics.py:305`) — 1e-12 keeps FP32 noise on
  the parity diagonal's structural zeros → the `ranks <= (3,5,3)` assert (`stab_tt.py:163`)
  **crashes on the first stabilizer.** Relax the drop to ~1e-6 (or build the tiny TT in c128).
- **`_FIT_TOL`** (`pepo/sampler.py:73` = 1e-12, the 97%-cost boundary fit),
  **`_NTU_REL_STOP`/`_NTU_PINV_RTOL`** (`dynamics.py:56-57`), **`bp_tol`** (`diagnostics.py:248`)
  — unreachable in FP32 → loops run to max-iters every call (**the speedup evaporates**); pinv
  rtol=1e-12 also **inverts noise directions → NaN/garbage in the NTU write-back**. Relax all to
  ~1e-6.

### (C) RE-DERIVE BY MEASUREMENT (not a guessed constant) — the runner floors
Per the declare+bound HARD constraint, these c64 floors must be **measured c64-vs-c128 gaps**, not
guessed:
- **`FLOOR_P0_MOVEMENT=1e-8`** (SW8 runner `:144`) — **the most insidious**: `p0` read through a
  c64 boundary fit floors at ~1e-7 even when truly converged → 1e-8 unsatisfiable → prerun walks
  χ_b to the 512 ceiling and every r=15 check fires escalation → **spurious PRECONDITION
  arm-falsification, no crash.** Re-derive to ~1e-5/1e-6.
- **`FLOOR_CROSS_ROUTE_D5` / `FLOOR_CHIB_DOUBLING = 1e-6`** (SW8 `:142-143`) — differences of two
  independent c64 contraction routes sit near/above 1e-6 → spurious `floors_close=False`.
  Re-derive (~1e-4/1e-5) from the measured route gap.

### (D) KEEP c128 (small islands, ~zero speed cost — and the validation baseline)
- The tiny **stab-TT build** (9^w, w≤4) + its structural rank asserts.
- The **leak Kraus + CPTP completeness checks** (`trajectory.py:388-391` CPTP_TOL=1e-12;
  `dynamics.py:99-106`; `sv_sampler.py:66,71` CPTP_TOL/WC_LEAK_COMPOSE_TOL) — operators are built
  in numpy c128 (`channels.py`) exact to ~1e-15; **keep the check c128, apply the c128 op onto the
  c64 state** (threading, not relaxing — a c64 residual ~1e-7 would false-trip 1e-12).
- The **NTU metric `g` + alternating-pinv refinement block** (`dynamics.py:786-819`) — it only
  refines VALUES *within the already-fixed rank* (`trajectory.py:483-484`), so keeping it c128
  costs ~nothing, does NOT move the bond-saturation rank, and preserves honest `ntu_eps`/
  `exact_rank` ledger values. (If instead run in c64, relax the pinv/stop tols per (B).)
- The **exact-route boundary reads** (`contraction.py:224-230,295-303`) and the **§6.2 residual
  instruments** (`contraction.py:386-448`) — these ARE the validation baseline; downcasting them
  destroys the oracle.

---

## 4. The four showstoppers for a naïve swap (fix before first run)

All four are fixable with dtype-aware ~1e-6 thresholds / the threading above:
1. `_exact_rank` collapses to full rank → (B).
2. stab-TT `ranks<=bounds` assert crash → (B).
3. CPTP/completeness asserts crash on operator downcast → (D) keep operators c128.
4. NTU-pinv rtol / fit tol at 1e-12 → speedup evaporates + noise inversion → (B).

---

## 5. Validation protocol (the BOUND — mandatory before ANY c64 number is believed)

The host RNG `u` is a **dtype-independent Python float** (`trajectory.py:728`,
`default_rng((seed,shot))`), so the c128 reference's branch selections can be **FORCED** in the
c64 replay → a clean frozen-branch comparison.

**FROZEN-BRANCH c128-vs-c64 replay** — require ALL of:
- **(a)** per-edge `r_dyn = _rank_for_tail(_insertion_spectrum(bond), 1e-8)` agrees within **±2
  every round**;
- **(b)** **mean(c64 − c128) rank ≥ 0** — guards the dangerous deflation direction; a c64 build
  reading systematically *below* c128 is **rejected**;
- **(c)** the c64 **noise floor stays < 1e-4·σ₀ every round** (if accumulation raises it into the
  1e-4 band, the read is corrupted → reject);
- **(d)** full sorted **singular-spectrum overlay** at the pilot's abort bond `B1_3` + the
  per-round max bond, agreeing down through the 1e-4·σ₀ threshold band;
- **(e)** `max|Δp0| ≤ ~1e-5` and the count of would-be free-sampling branch flips ≈ 0;
- **(f)** **eps-band** {5e-9, 1e-8, 2e-8}: the saturation TREND (rank vs round) qualitatively
  identical across the band (c64 cannot resolve eps=1e-8 better than tens-of-%);
- the **d3 gate suite** (exact) still passes with the raised thresholds; the codestate
  **`|2>`-mass reads EXACTLY 0** (structural zero — must survive the cast);
- **(g) DIRECTION-SIGN gate on the verdict** (§0): c64 "grows" → trigger; c64 "bounded/GO" →
  confirm in c128 at the same rounds before reporting.

---

## 6. Epistemic classing

The c64 engine's outputs are **class (c) heuristic SCREENING** — never (a) or (b). The bound is
the frozen-replay agreement numbers of §5. c128 remains the evidence engine; any load-bearing
conclusion is certified in c128.

---

## 7. Effort, sequencing, and the spark corollary

- **Effort:** a focused mini-project — dtype threading across ~4 files (`state.py`,
  `contraction.py`, `dynamics.py`, `trajectory.py` + the SW8 runner) + tolerance parametrization
  + the frozen-replay validation harness. **Not a flag flip; not a rewrite.** Run it under the
  `contract-build` discipline (contract-first, adversarial gates, killer tests on the raised
  thresholds).
- **Sequencing (gated on the c128 triage):**
  - triage = "artifact/continue" **AND** a 20–30 round run is needed → **build it**;
  - triage = "No-Go / bond grows unbounded" → **shelve** (nothing to accelerate);
  - triage = "saturates at low bond, c128 affordable" → may **not be needed**.
- **spark corollary:** GB10's *c128* large-matrix linalg is known-garbage (residual 1.0 at
  1024², memory `reference-ssh-spark-compute`), but its **c64** large linalg was **never tested**
  and FP32 is GB10's strength. If the c64 build validates on the 5090, it becomes worth a
  one-shot GB10 c64-reliability probe — c64 could unlock spark's fast FP32 + 119 GB (off the live
  desktop). Secondary; only after the 5090 c64 build passes §5.
