# Rung-1 PEPO Engine — Build Contract (contract-first; binding for builders A1–A4)

Status: CONTRACT v1, 2026-07-09. Governing registration: `pepo_d5d7_carrier_prereg.md` v2.2
(gates G1.1–G1.9, ledger C1–C10, simplifications S1–S11, rung-0 outcomes). This document pins
IMPLEMENTATION semantics: representation, invariants, the op↔referee registry, gate protocols,
and scope fences. Committed BEFORE any implementation code. A miss at a gate is a finding to
adjudicate, never a silent tolerance bump.

## 0. Verified structural facts (Stage-0 ledger — each checked in the named seam, 2026-07-09)

| # | Fact | Verified at |
|---|---|---|
| F1 | The compiled within-cycle dynamics is ENTIRELY single-qudit: per-position token streams `H`/`X`/`LEAK` pre-M, transversal `Y` post-M (skipped on the terminal round); unknown tokens raise | `QutritDM.apply_within_cycle_premeasure` / `apply_within_cycle_postmeasure` (docstrings + code, carrier/exact/qutrit_dm.py) |
| F2 | The stabilizer measurement is the ONLY multi-site operation: X-supports Hadamard-rotated to Z (leaked levels H-inert), then the DIAGONAL syndrome-bit POVM `E_s[i,i] = ½(1+(−1)^s ∏_q d_q)` with per-site weights d_q = +1 (t=0), −1 (t=1), 1−2b (t≥2, arm A/C), applied elementwise as ρ[i,j] → √e_i √e_j ρ[i,j] (unnormalized), then rotated back | `QutritDM._povm_diag_weight` + `project_stabilizer` |
| F3 | Non-selective round = sum of the two √E_s branches per stabilizer, sequentially over the 8 stabs (the R-gate reference run's exact loop) | `outputs/nonpauli_teacher/pepo_feasibility_drho_vs_round_d3.py` main loop |
| F4 | Leak channel = per-CZ-layer single-qudit Kraus list `exp(L/4)` `(n_kraus,3,3)`, marshalled per position with the token streams | `SvSampler.build_within_cycle_leak` / `marshal_within_cycle` → `WithinCycleMarshalled.leak_kraus`, `streams_by_pos` |
| F5 | The d3 patch layout is the rotated DIAMOND; data_coords transform to an integer d×d grid under u=(x+y)/2, v=(x−y)/2 (to be ASSERTED at runtime, not assumed); stabilizer supports are 2×2 plaquettes (weight 4) + boundary weight-2 pairs; bisection n_cross = d−1 (rung-0 counted+measured); s_t = 2·n_cross at every straight cut | rung-0 `pepo_rung0_ncross_dbond_d357_result.json` + `xzzx_parser` coords |
| F6 | The NTU metric with rows = the BRA insertion satisfies ε = v†gv (the rung-0 C4-caught convention); structured Fig.-4 assembly == dense at ~5e-16 | `pepo_rung0_ntu_metric_unit.py` (fixed revision, content_hash b5f4f834…) |
| F7 | quimb 1.14.0 preserves torch-cuda-complex128 backing through PEPS contraction; PEPS/PEPO/TensorNetwork2D + `contract_boundary_from*` exist | rung-0 substrate probe (E1/E2) |
| F8 | The frozen G1.2 referee numbers (sequential-null detector marginals, ε*-cut χ=16, worst dp/bar=0.0167) live in `outputs/nonpauli_teacher/pepo_record_error_vs_eps_d3_result.json`; the sequential-null convention is DEFINED BY `pepo_record_error_vs_eps_d3.py` (reuse verbatim, cite by script name) | that script + JSON |
| F9 | Codestate oracle init = `QutritDM.set_code(...)` + `init_logical(m)`; trace==1 asserted there | qutrit_dm.py + the R-gate script |

## 1. Modules + ownership (src placement user-confirmed 2026-07-09)

```
src/error_coupling_simulator/carrier/pepo/
  __init__.py        (public API re-exports)
  layout.py     [A1] diamond→grid transform + plaquette paths + codestate PEPO builder
  dynamics.py   [A2] single-site superops, stabilizer-channel TT, NTU truncation, ledgers
  sampler.py    [A3] boundary-MPS norm cache, Tr(ρ·Π̂) caps, Born sampling + selective update
  README.md          module scope (per repo convention)
tests/test_pepo_rung1.py            [test-builder] the registered gates vs THIS contract
outputs/nonpauli_teacher/pepo_rung1_*.py  [A4] the GPU gate/cert scripts + runners
```

Builders are BANNED from GPU/pytest execution (static checks + `py_compile` +
`--collect-only` only); evidence runs are orchestrator-serialized. The test builder writes
against THIS CONTRACT, never the implementation; ambiguous signatures get ONE adapter at the
top of the test file.

## 2. Representation + invariants

- **State object `PepoState`**: a quimb `TensorNetwork` of rank≤5 site tensors, one per data
  qutrit, physical leg = the FUSED d²=9 vectorized index (ket⊗bra, ROW-MAJOR vec: fused index
  k = 3·t_ket + t_bra — pinned; every superoperator uses this convention), virtual bonds on
  the (u,v) grid edges. Tensors torch-cuda-complex128 ALWAYS (S8; assert at construction).
- **Grid**: u=(x+y)/2, v=(x−y)/2 from `sched.data_coords`, integrality/uniqueness/d×d-ness
  ASSERTED (F5). Site tags `Q{pos}` keyed by ENGINE position (the streams/stab key space).
- **No global gauge/canonical form is tracked** (2D has none — Kilda App. A.1); the ONLY
  tracked bond metadata is the per-bond dimension + the truncation LEDGER: per-truncation
  discarded weight (squared-σ scale — UNITS: discarded = Σ_cut σ_k² / Σσ², the same squared
  convention as the rung-0/R-gate scripts) and per-round trace shift.
- **Invariants (constraint-ledger C1–C4 bindings, checked where stated):**
  - trace: `pepo_trace(state)` == 1 within the logged trace-shift ledger after every round
    (C1); Hermiticity of the represented ρ is NOT tracked per-tensor (the fused-leg PEPO does
    not expose it locally); it is checked at gates via the d3 dense reconstruction (G1.9 path)
    and via real-nonnegative Born weights (C3 witness) — pinned here so nobody "adds" a bogus
    local Hermiticity assert that a correct fused representation would fail.
  - positivity: NEVER assumed; the C3 witness (Born weight < −1e-8 logged; cumulative
    negative mass > 1e-4 STOP) is implemented in sampler.py and is non-optional.
- **Bond caps**: D_cap per run config; rung-1 gates run the D-sweep {2,4,8,16} (rung-0
  pinned). NO silent cap: hitting the cap with discarded > the gap tail is logged as
  CAP_BINDING in the ledger.

## 3. Op ↔ referee registry (every op names its equivalence target + exact semantics)

| Op (module) | Semantics (pinned) | Referee (equivalence target) |
|---|---|---|
| `build_codestate(sched, m)` [layout] | ∏_g (I+g)/2 · logical-projector · \|0…0⟩-analog as W-tensor chains (D-P construction: per check ONE chain, one inter-column bond, bond 2 state / 4 operator fused); qutrit-embedded (\|2⟩ row zero); built directly as the FUSED-leg PEPO of ρ = \|m⟩⟨m\| | d3: dense reconstruction == `QutritDM.init_logical(m)`.rho, max-abs ≤ 1e-12 (G1.3 pre-check); all d: structural exacts ⟨S_g⟩=+1, ⟨Z_L⟩=(−1)^m, \|2⟩-mass=0 via sampler caps (C5) |
| `apply_token_stream(state, streams, leak_kraus)` [A2] | F1 semantics VERBATIM: per position, tokens in order, stop at `M`; `H`→qutrit Hadamard superop, `X`→X superop, `LEAK`→Kraus-sum superop Σ_k (K_k ⊗ K̄_k) on the fused leg; `Y` ignored pre-M; unknown token raises. Single-site: NO bond change (assert) | `QutritDM.apply_within_cycle_premeasure` — d3 dense equality per token type on random small states (unit gate, 1e-12) |
| `apply_postmeasure(state, streams, terminal)` [A2] | F1: post-M `Y` per position; terminal skips; non-Y post-M token raises | `QutritDM.apply_within_cycle_postmeasure`, same bar |
| `stab_channel_tt(paulis, outcome, b, arm)` [A2] | The EXACT NUMERIC TT of the diagonal fused-leg superoperator of √E_s·(·)·√E_s over the support: build the 3^w diagonal e_i from the F2 formula (w = weight ≤ 4 → ≤ 81 entries), take √, form the fused diagonal √e_i·√e_j (9^w entries, w≤4 → ≤ 6561), TT-decompose EXACTLY (SVD, zero-tol NUMERICAL_ZERO) along the plaquette path; assert TT rank ≤ 10 per bond (measured, logged). X-supports: sandwich with single-site H superops (F2), NOT folded into the TT | `QutritDM.project_stabilizer(..., diagonal_z=False)` — d3 dense equality of one full stabilizer update on random ρ, 1e-12; the b/arm table of `_povm_diag_weight` is the normative formula (arm A default, b from the p1c cell = 0.9) |
| `nonselective_round(state, stabs, …)` [A2] | F3 loop: per stab, branch-sum ρ → √E_0ρ√E_0 + √E_1ρ√E_1 (PEPO add = bond-double on the support path) then NTU gap-cut truncate; stabs in the SAME order as `sched.stabilizers` | R-gate reference loop semantics; gate-level: G1.2/G1.3 vs the frozen JSONs |
| `ntu_truncate(state, bond, D_cap)` [A2] | The rung-0 seed: NTU metric (rows = BRA insertion, F6), pinv optimization loop, GAP-CUT selection (cut at the largest spectral-gap ratio ≥ the registered gap-detection rule: cut index = argmax σ_k/σ_{k+1} within k ≤ D_cap, tie→smaller k; if no ratio ≥ 10, fall back to D_cap and log CAP_BINDING) — the gap rule is pinned HERE to stop drift | rung-0 unit (metric); gate-level G1.3 (gap rank == 16 at d3) |
| `norm_cache(state)` / `expect_diag_caps(state, caps)` [A3] | Rudolph–Tindall reverse-pass boundary-MPS over grid columns (one-site fitting, dim R_n), cached once per state; Tr(ρ·⊗diag-caps) via capped physical legs (trace-cap = Σ_k fused (k,k)) | d3: dense Tr(ρ·Π) equality 1e-10; convergence-in-R_n logged |
| `born_sample_round(state, stabs, rng)` [A3] | Per stab sequentially: q = Tr(E_s ρ)/Tr(ρ) via caps; sample; SELECTIVE update √E_s branch + renormalize ledger; emit detector bits per the SAME detector convention as the 1D engine (`seam.py` d3 conventions) | d3 G1.1: per-sampled-record exact probability from the DM oracle path propagation (`p7e_carrier_cert_common.DMPathEvaluator` reuse), z ≤ 4 |
| latent conditioning [A3, G1.6 only] | Per-sample latent draw OUTSIDE the TN; per-round Pauli superop insertion per arm; χ(mix)=χ(arm) check | X2b d3 evidence pattern (`pepo_xi_correlation_length_d3.py` X2b arm) |

**Units table**: b ∈ [0,1] probability; discarded weight + ε levels are SQUARED-σ scale;
dp bar = z·√(p(1−p)/N) at N=1e6, z=4 (per-detector, the record-gate convention); NTU ε is a
squared norm (F6 quadratic form); gap-cut ratio is on UNSQUARED σ_k.

## 4. Registered gate protocols (predictions: ALL PASS; tolerances pinned)

- **G1.0 (pre-gate, A1)** dense d3 codestate == oracle (1e-12 max-abs).
- **G1.1** N=1e6 sampled {det,obs} records @ d3, R=3, p1c cell; per-record exact probability
  via DMPathEvaluator; multinomial z ≤ 4 on the top-64 record classes + tail-mass bucket.
- **G1.2** sequential-null detector marginals, R=10 == frozen F8 table: engine worst
  dp/bar ≤ 0.1 (bar convention above).
- **G1.3** engine gap rank at the straight d3 bisection == 16 EXACTLY at every round 1..10.
- **G1.4** Δσ (straight-cut kept spectrum, zero-padded, R≤2 excluded) plateaus ≤ 1e-3;
  discarded-weight plateau; D-sweep {2,4,8,16}: oracle distance monotone non-increasing in D
  (Kilda-pattern destabilization ⇒ STOP finding).
- **G1.5** controls DEMONSTRATED to trip: CorruptStab (wrong support) breaks G1.0/G1.2;
  Shuffle (permuted schedule) breaks G1.2; identical-arms guard in every two-arm compare;
  each C1–C10 broken-variant fires (test-builder owns the sabotage variants, K-catalog
  discipline).
- **G1.6** χ(mix) == χ(arm) per round (latent bond-free), d3.
- **G1.7** in-engine ξ re-measure (the ξ-gate instrument, NO_FIT policy per prereg P4):
  ξ(Zq) ∈ [0.2,0.8], ξ(n2) ∈ [0.1,0.5].
- **G1.8** window-embedding mismatch calibration: embedded 2×3/3×2 windows of d3 vs
  stand-alone tiles, both via the DENSE oracle (this is an ORACLE-side deliverable — no PEPO
  code in the loop; its output is the S11 bound number).
- **G1.9** positivity: min-eig of the dense-reconstructed truncated ρ (d3) within
  \|λ_min\| ≤ 1e-6; the sampler's negativity witness fires on a sign-flip sabotage.

## 5. Scope fences (rung-1)

d3 ONLY (no d5 tile — rung 2); the record-law arm (non-selective) and the sampling arm are
BOTH in scope (G1.2 vs G1.1); memory latent only as far as G1.6; NO performance targets
(correctness rung); NO d7 objects; the S10 compiled-circuit scope binds everything; src
commits wait for explicit user confirmation (one reviewed diff), docs/outputs flow normally.

## 6. Red-team + build protocol

Stage-2: ≥2 un-led adversarial passes on THIS contract (contract + referee seams; break it:
un-certifiable claims, unpinned semantics, checks a correct implementation would fail);
loop to zero blockers before any builder starts. Stage-3: A1/A2/A3 disjoint files, test
builder parallel from the contract. Stage-4: multi-lens un-led review (correctness /
numerics-GPU / devious-vacuity) + independent refute-verification of every finding, fixes
BEFORE the first GPU run. Stage-5: committed runners, sha256 + PIPESTATUS discipline.
Stage-6: KILLER variants per load-bearing assert. Stage-7: OUTCOMES backfilled here + into
the prereg; CODE_MAP regenerated; README added.
