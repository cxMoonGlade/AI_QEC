# Stage-2 src contract — environment-aware rank selection in the PEPS truncator (2026-07-11)

> **The product.** Stage-1 confirmed Γ-independently that the per-edge bond is massively
> over-counted and the exact environment removes it losslessly (leak-off B4_6 dim16→env_rank1,
> `S_A==GF(2)` to 1e-15, overlap 1.0). Stage-2 wires that into the carrier truncator as a NEW
> mode, so the represented bond tracks the bounded physical entanglement. **Stage-2a = d3-first
> (exact Γ); Stage-2b = d5 (boundary-MPS Γ)** — this contract covers 2a.
>
> Epistemic classes per `docs/METRICS.md`: (a) exact, (b) prediction band, (c) gate/decision rule.

## 1. Scope + the load-bearing insight
The over-count enters at RANK SELECTION: `_policy_cut` (trajectory.py) sets
`kept_target = _rank_for_tail(_insertion_spectrum, ε)` from the LOCAL pair-insertion spectrum.
Fix: a NEW truncation mode whose `kept_target` = the **environment-optimal rank** (smallest χ
with the FET environment fidelity `Fid_Γ(χ) ≥ 1−EPS_FID`), computed from the bond's exact
double-layer environment `Γ` via the multi-restart FET solver validated in Stage-1.

**ADD a mode, do NOT change existing ones.** New `TruncationPolicy("fet_env", eps_fid=1e-8)`.
The `dynamic_eps` / `lossless` / `d_cap` arms are UNTOUCHED ⇒ the current d3 gates
(`tests/test_peps_spike.py`, 28/28) stay BYTE-IDENTICAL (verified by re-run, not asserted).

## 2. What is LIFTED from the Stage-1 diagnostic (validated) into src
Into a new module `src/error_coupling_simulator/carrier/peps/fet.py` (referenced by
`trajectory.py`); lifted VERBATIM-then-adapted from `outputs/nonpauli_teacher/fet_stage1_env_truncation.py`:
- `gamma_TN(state, bond)` — the exact double-layer single-bond environment `Γ[i,I,j,J]`
  (mirrors `expect_double_layer`'s exact branch + the bond split). **d3 exact; d5 = Stage-2b.**
- the multi-restart FET M1 solver: `gamma_fidelity`, `_als_inner`, `_fix_gauge`, `fet_m2`,
  `_carrier_svd_seed`, `build_seeds`, `fet_m1` — env-optimal `(U_χ,V†_χ)` + `Fid_Γ`.
- `apply_fet_truncation(state, bond, U, Vh)` — the write-back (mirrors `ntu_truncate` layout).
- `env_optimal_rank(state, bond, eps_fid)` — NEW thin wrapper: sweep χ, return the smallest χ
  with `Fid_Γ(χ) ≥ 1−eps_fid` + its `(U,V†)`.
The Stage-1 `gamma_dense` (independent route) is lifted too but ONLY into the TEST (the
anti-circular referee), never the src hot path.

## 3. The seam (per-op table) — BOTH passes pinned (RT F1/F2)
The two-pass `truncate_path_bonds` runs pass-1 `_policy_precut` over ALL bonds, THEN pass-2
`_policy_cut` over ALL bonds. `fet_env` must be pinned in BOTH:

- **`_policy_precut` — fet_env is a strict NO-OP (RT F1 blocker).** Add an early-return branch
  `if policy.mode == "fet_env":` that returns a rec with EXACTLY the keys `_policy_cut`'s
  summary reads (`precut_discarded=0.0, r_dyn=None, width=None, window_binding=False,
  exact_rank=_exact_rank(_insertion_spectrum(bond))`) and does NO `svd_precut_bond`. Pass-1
  MUST leave the bond at full dim so pass-2 `gamma_TN` reads the UN-pre-truncated environment.
  (Without this, `fet_env` falls through to the `dynamic_eps` tail → `float(policy.eps_spike)`
  = `float(None)` → TypeError on the first stabilizer; and a naive `eps_spike` patch would
  double-truncate the FET's own input.)

- **`_policy_cut` — fet_env does the WHOLE truncation, PER-BOND SEQUENTIAL on the CURRENT
  post-write state (RT F2 — NOT per-bond independent).** `if policy.mode == "fet_env":`
  `Γ = gamma_TN(state, bond)` (on the state left by the PRIOR bond's write-back) →
  `env_rank, U, Vh = env_optimal_rank(state, bond, policy.eps_fid)` →
  `apply_fet_truncation(state, bond, U, Vh)`. Because `truncate_path_bonds` calls `_policy_cut`
  over bonds IN ORDER, each bond's Γ reflects already-truncated neighbours — this is
  LOAD-BEARING: the joint rank-4 cut entanglement is distributed across edges as they truncate
  (the first edge → ~1, later edges retain more). A read-all-in-pass-1-then-write scheme would
  truncate EVERY edge to its trivially-~1 "given-others-full" rank and DESTROY the entanglement
  (G-FET-FAITHFUL would then fail). The sweep ORDER is fixed + recorded (Stage-1 F7).

- ledger entry `op="fet_truncate"` with `dim_in, env_rank, Fid_Γ, eps_fid` (+ the summary keys
  above). `TruncationPolicy.__post_init__` validates `eps_fid > 0` for the new mode.

## 4. Representation + invariants (pre/post, ASSERTED)
- `Γ` Hermitian PSD in the LAYER grouping (Stage-1 G-Γ-HERM); `einsum("iIiI",Γ)==⟨ψ|ψ⟩`.
- `env_rank ≤ bare_rank` always (the FET never keeps MORE than the local rank).
- write-back is state-faithful at `env_rank`: the applied truncation's `Fid_Γ ≥ 1−eps_fid`.
- **No-qualifying-χ fallback (RT F5):** if NO `χ ∈ [1, bare_rank]` reaches `Fid_Γ ≥ 1−eps_fid`,
  `env_optimal_rank` KEEPS the full bond (`env_rank = current dim, no truncation`) — it must
  NOT fall back to a lossy `CHI_CAP` ceiling cut (that would violate the invariant above and
  MASK a non-collapse as faithful). WP1' then HONESTLY reports the bond as non-collapsing.
  Any per-bond χ-search ceiling is a declared (c) resource guard `≥ bare_rank`, never a silent
  truncation.
- `fet_env` NEVER runs on the d3 EXACT-referee gates (they use `dynamic_eps`/`lossless`).

## 5. REGISTERED GATES (predict-before-measure)
| id | class | prediction | how |
|---|---|---|---|
| G-D3-IDENTICAL | (a) | existing 28/28 d3 gates byte-identical | re-run `peps_spike_gates_d3_run.sh`, hash-compare (new mode unused there) |
| G-FAITHFUL-GOLD | (a) | **the exact cumulative truncation fidelity** `|⟨ψ_ref_R\|ψ_trunc_R⟩|² ≥ 1−1e-6`, from a PAIRED untruncated same-RNG reference trajectory (RT F4 — the product is NOT the true cumulative) | test: run `fet_env` + a same-`base_seed`/`fit_seed` lossless-no-FET reference, overlap via `dense_psi` each round (capped à la Stage-1 GOLD) |
| G-FAITHFUL-PRIMARY | (c) | per-round before/after `fid_sweep_r ≥ 1−1e-8` (product = a LOWER-BOUND proxy, not the true cumulative — decision gate only) | per-round `dense_psi` before/after-sweep overlap |
| G-SA-CORROB | (a) | post-round `S_A == GF(2) baseline` (leak-off; CORROBORATION, not the primary faithfulness read — it is implied by GOLD in the lossless regime) | `dense_psi` S_A vs GF(2) |
| G-WP1'-BOUNDED | (b) | **the joint max per-edge bond stays BOUNDED (≤8) and SATURATES across R=12 rounds** under `fet_env`, state faithful | the src truncator run (the joint test Stage-1 never reached); leak-off first |
| G-ANTICIRC | (a) | in the test, `Γ_TN==Γ_dense` (two routes) + `Fid_Γ==fid_dense` on the real bonds | test-only referee (`gamma_dense` + `dense_psi`), the Stage-1 anti-circular check |

**Fork resolved by G-WP1'-BOUNDED:** bounded+saturating+faithful ⇒ the single-sweep-per-stab
env-aware truncator is sufficient (Stage-2 lands); if it grows, escalate to an iterative
multi-sweep (contingent, per Stage-1 §0 outcome 2/3).

## 6. Scope fences
- NO d5 (Stage-2b — needs the boundary-MPS single-bond Γ; this contract is exact-d3 Γ only).
- NO change to `dynamic_eps`/`lossless`/`d_cap` behavior (byte-identity depends on it).
- NO leak-on scope change (leak-off first; leak-on is conditional on carrier forward faithfulness).
- The FET solver is LIFTED (validated in Stage-1), NOT re-derived; `gamma_dense` stays test-only.
- **`fet_env` is a FEASIBILITY/diagnostic mode, NOT a production data-generation sampler path
  (RT F8):** `gamma_TN` recomputes a full double-layer `auto-hq` contraction per call, so
  `fet_env` is orders slower than `dynamic_eps`/`lossless` — fine for the 1-shot WP1'/faithfulness
  gates, not for N-shot production. Declared cost regime; a future optimization (cache the
  contraction path per topology, cap the χ-search) is out of scope for 2a.

## 7. DISCIPLINE
Mainline src ⇒ contract-build (this contract + ONE red-team round + disjoint build/review +
review-before-run). src commits need EXPLICIT user confirmation; one reviewed diff. NO
co-author. The independent-GT referee (`gamma_dense`, `dense_psi` S_A, GF(2)) shares no code
with the `fet.py` hot path it referees. Match rigor to load-bearing — ONE red-team round, then
build; do not spiral (the Stage-1 lesson).
