# Batched-MPS trajectory backend — groundwork + pre-registration (2026-07-06)

**The MPS-scaling workstream** (supersedes the TJM line as the scaling bet — `tjm_parallel_backend_prereg.md`'s
P-OPT2, now literature-grounded on the six in-repo notes: `patti_ptsbe_2504.16297`, `doi_batch_shots_gpu_2308.03399`,
`jiang_bqsim_gpu_batch_dd_2503_asplos`, `zhang_tensorcircuit_ng_2602.14167`, `schieffer_cudaq_mps_2501.15939`,
`patti_batched_tn_sampling_2604.08467`; 3-agent extraction vs the verified `mps_forward.py` op inventory).

## 0. Grounded verdict
1. **The disease** is unanimous across the systems notes: per-op dispatch overhead ≫ tensor work at our sizes
   (Schieffer: MPS-GPU 33% activity, <1% TensorCores, 128-B transfers, 70% SVD phase; Patti: dispatch/path overhead
   10²–10⁷× the contraction). Our measured d3 ~1 s/shot / d5 ~104 s/shot serial quimb loop is this disease.
2. **The divergence question resolves cleanly**: PTSBE does NOT handle mid-circuit measurement and its pre-sampling
   is exact only for state-INdependent (unitary-mixture) noise — our MCWF Kraus norms are state-dependent, so naive
   pre-sampling samples the WRONG measure. Shot-branching blows up under immediate divergence (ours: ~24 Kraus + 8
   Born collapses per round). **Batch-shots (Doi) — every shot owns a state slot, uniform kernels, per-shot masks —
   is the divergence-robust pattern, and is what our dense `sv_traj_d3.cu` already does** (W=1024 waves).
3. **The decisive structural fact (verified in source):** our op stream is SHOT-INDEPENDENT — per-shot divergence
   lives only in operator VALUES (which Kraus, which √E_s candidate, which collapse), never in control flow. Every
   shot runs the identical ~70–90-op sequence per round ⇒ batching = a leading batch dim on every MPS tensor
   ``[B, χl, 3, χr]`` + gathers; no padding tricks, no branch trees.
4. **Op enumeration:** ~60–80 ops/round batch trivially (1-site gates/Kraus via batched einsum; Kraus SELECTION =
   batched branch norms + per-shot gather — Doi's Kraus-batch pattern; ≤4-site expectations; terminal readout).
   The 8 per-round **√E_s recompressions are the load-bearing op**: cuSOLVER has NO batch-parallel dense SVD at
   192–768 (gesvdjBatched caps at 32×32) ⇒ torch may LOOP the batch. Two levers: (i) **at d3 exact grade no rank
   selection is needed at all** (`_apply_sqrt_Es` already special-cases χ ≥ exact_chi) ⇒ **batched QR
   (geqrfBatched, truly batch-parallel) replaces SVD**; (ii) at d5, Gram-matrix + `cusolverDnXsyevBatched`.
5. **Framework alternatives:** TC-NG has the one published end-to-end batched-MPS-trajectory number (MIPT 20q/40L
   χ=16 vmap: 0.084 s/traj on H200 — a near-isomorphic workload) but **complex128 MPSCircuit support is UNVERIFIED**
   (hard gate) and its own note says a full port may beat interop; cuTensorNet-MPS exposes no batched-state mode in
   the evaluated surface and its benchmarks are complex64 (non-transferable). ⇒ **PRIMARY: hand-rolled torch
   batched-MPS sibling arm** (stays in our torch/cuda/c128 world, zero new dependency, pristine-baseline clean);
   TC-NG = benchmark reference + fallback pending an x64 check.
6. **Physical ceiling declared:** once launch-bound overhead is gone, complex128 on the RTX 5090 is FP64-throughput
   bound (~1.6 TFLOP/s, 1/64 of FP32). All estimates below carry this; a c64 arm would need its own Gate-5-style
   equivalence gate (NOT registered here).

## 1. Phases + registered gates
- **OPT2-0 — on-box decomposition spike (GPU, minutes; BEFORE any backend code).** Microbench on OUR card:
  torch batched `linalg.svd`/`qr` dispatch reality at ``[B, 192..768]`` c128 (loop vs batch), `geqrfBatched`
  reach, `cusolverDnXsyevBatched` exposure, gesvd-driver robustness on stabilizer-flat spectra under batch.
  Registered outputs: measured ms/op tables → the phase gates below get ANCHORED throughput bands (the class-(b)
  estimates in §2 are pre-spike and say so).
- **OPT2-1 — batched-MPS op core (src, sibling module; quimb-free).** Batched 1-site apply/RDM/Kraus-gather/
  renormalize, ≤4-site local expectation, √E_s blob apply, QR-exact-grade recompression. Gates (a): per-op value
  equivalence vs the serial quimb arm ≤1e-12 on random states (both χ grades), all ops.
- **OPT2-2 — the batched trajectory driver @ d3 exact grade.** Same drop-in seam as the TJM prereg's P-TJM0
  contract (RunSpec/sched/leak in → ShotSet out); serial arm untouched. Gates: statistical equivalence vs the
  serial arm at matched physics (marginals z ≤ 4; record gates vs the DM oracle use the SEQUENTIAL null — the
  P1-c machinery); norm/ledger health; **bit-identity is DIAGNOSTIC ONLY** (batched reduction order legitimately
  flips knife-edge Born comparisons — registered, never a silent pass/fail). Throughput gate (b, pre-spike):
  ≥50× serial at B=1024 (estimate 100–300× if QR-grade lands, ~6–20× if SVD loops — the spike adjudicates).
- **OPT2-3 — d5 fixed-χ arm.** Pad-to-cap fixed shapes; per-shot discarded-weight ledger semantics preserved
  (`MpsTruncationLedger` per shot); Gram+Xsyev lever if the spike says so. Gates: sub-register DM tiles + serial-arm
  statistical equivalence; throughput band registered post-spike (pre-spike estimate 85–400× vs 104 s/shot).
- **Conjunction tie-in:** the batched arm is the production carrier for P2's per-round leakage wiring at d5 — the
  P2 per-round leak slices are op-VALUE changes on the same control flow, exactly what the batch structure carries
  for free.

## 2. Registered predictions (class (b), PRE-SPIKE — OPT2-0 re-anchors them)
- P-B1: batched d3 exact-grade ≈ 1–5 ms/shot at B=1024 (state ≈ 2.9 GB) IF batched-QR lands; ~6–20× serial if the
  decomposition loops. P-B2: d5 χ≤256, B=128 (state ≈ 10 GB): ~0.3–1.2 s/shot. P-B3: memory model B·L·χ²·16 B +
  transient blob ~85 MB/shot at d5 (fits the card at the stated B). P-B4: certification — batched-vs-serial alone
  is NOT sufficient (shared quimb-lineage blind spots); the DM record_oracle sub-register seam + stim/closed-form
  anchors + CorruptStab/Shuffle controls are non-optional (FAITHFULNESS_PROTOCOL; the Gate-4 lesson).

## OPT2-0 OUTCOMES (2026-07-06 run — `opt2_0_decomposition_spike.py` hash 0179decb…, RTX 5090, torch 2.12/cu130)
- **S-1 CONFIRMED:** `torch.linalg.svd` is batch-LOOPED at every relevant size/driver (gain ~1.0×; per-item
  gesvd 51 ms / default 232 ms at n=243) ⇒ SVD stays out of the hot path entirely.
- **S-3 = THE LEVER:** batched `eigh` is genuinely batch-parallel — **18.7× gain at n=192 (0.32 ms/item),
  13.1× at n=243 (0.54 ms/item), 4.0–5.8× at 512–729 (2.9–7.4 ms/item)** ⇒ **Gram + batched-eigh replaces SVD**
  for recompression at BOTH d3 and d5. Gram's κ² cost is benign for truncation (the tail we discard is what
  underflows; discarded-weight ledger tail below ~1e-14 in σ declared at the NUMERICAL_ZERO floor).
- **S-2 partial:** batched QR gains only 1.5–1.8× (n≤243), but its ABSOLUTE cost (2.8–4.4 ms/item) is 12–18×
  under gesvd — the d3 exact-grade fallback stands, Gram+eigh preferred everywhere.
- **S-4:** no driver hard-errors on stabilizer-flat spectra on this stack (the old cusolver failure did not
  reproduce); gesvd is 15–30× faster than default/gesvdj on flat spectra — reconfirmed for any residual SVD use.
- **S-5:** batched c128 GEMM at **1.54–1.72 TFLOP/s ≈ the FP64 ceiling** — the trivially-batched ~60–80 ops/round
  will run at speed-of-light.
- **ANCHORED BANDS (replace the §2 pre-spike estimates):** d3 batched ≈ **10–100× serial** (the pre-spike
  100–300× optimistic end is retired: eigh/QR per-item is ms-scale, not µs; recompression ≈ 8×(Gram GEMM +
  0.5 ms eigh)/round dominates); d5 ≈ **100–300× serial** (2.9–7.4 ms/item eigh vs the catastrophic 104 s/shot
  serial baseline — the win is largest exactly at the scale that needs it). OPT2-2/3 gates use these bands.

## 3. Disciplines
Every phase src needs user commit confirmation; committed scripts + runners (aiqec bin on PATH); GPU serial;
un-led review before every gate run; CODE_MAP regen per src change. TJM prereg stays on file (its registered
tie-or-lose bet unaffected); this doc owns the scaling line.

## OPT2-1 DESIGN — build contract (2026-07-06, written BEFORE code; theory-first)

**Module:** `src/qec_twin/forward/scalable/batched_mps.py` — quimb-free sibling of `mps_forward.py`
(the serial arm stays UNTOUCHED; quimb appears only in the equivalence TESTS as the reference arm).
Torch/cuda/complex128 only. Tests: `tests/test_batched_mps_ops.py` (`requires_cuda` skip convention).

### D-1 Representation (fixed shapes — the batch-shots invariant)  [v2 2026-07-06 post red-team]
`BatchedMps`: `n` site tensors, site `k` = `[B, cap_{k-1}, 3, cap_k]` (boundary caps = 1), where
`cap_k = min(3^(k+1), 3^(n-k-1), chi)` for internal cut `k = 0..n-2`. Tensors are ZERO-PADDED to cap
shapes at all times. PADDING/ISOMETRY CONVENTION (pinned; red-team A-1): the invariant is precisely
(i) the CENTER tensor and every absorbed R/M factor carry exact-zero padded channels (this is what
keeps the represented state unchanged — class (a) identity), (ii) isometry factors are isometric ON
THE UNPADDED SUBSPACE (reduced QR of a rank-deficient padded matrix returns arbitrary orthonormal
completions in padded columns — they multiply zero rows of R, harmless), (iii) factor columns
produced by the Gram path beyond the computed rank are EXPLICITLY ZEROED (partial isometry). Code
asserts target (i)+(iii), never literal full isometry. Structural fact (assert in code):
`cap_k <= 3*cap_{k-1}` and `cap_{k-1} <= 3*cap_k` always, so reduced batched QR at cap shapes
returns cap-shaped factors — shapes NEVER change during a run (uniform kernels, Doi batch-shots).
An explicit orthogonality-`center` invariant is tracked; EVERY op declares its center pre/post
condition (the D-2 center table) — reads AND the window op canonicalize first; the per-shot
NON-unitary 1-site forms (Kraus gather, projectors, terminal collapse) REQUIRE center == site
(enforced by canonicalizing, not by trusting the caller).

### D-2 Op set + exact semantics (each op names its serial referee)
1. `bond_caps(n, chi)`; `from_dense(psi[B,3^n])` (exact sequential split; ASSERTS rank <= caps —
   from_dense is for construction/tests, never a truncation path); `broadcast_from_quimb(mps, B)`;
   `to_dense() -> [B,3^n]` (test-scale only). Referee: quimb `from_dense`/`to_dense`.
2. `canonicalize_(center)`, `norm_sq() -> [B]`, `renormalize_()`. Referee: `_norm_sq`/`_renormalize`.
3. `apply_1site_(U, site)` — `U` shared `[3,3]` OR per-shot `[B,3,3]` (the gather form Kraus/collapse
   needs). Referee: `_apply_gate`.
4. `site_rdm(site, normalized=False) -> [B,3,3]` — the 1-site RDM at the center (unnormalized
   default = the serial branch-norm convention `normalized=False`). Referee: `local_expectation_canonical`.
5. `kraus_sample_(kraus[K,3,3], site, u[B]) -> (sel[B], pk[B,K])` — `pk = Tr[K^H K rho]` from the RDM;
   selection = the serial cumulative rule EXACTLY: first `k` with `u*tot <= cumsum_k`, fallback `K-1`;
   gather selected Kraus per shot; apply; renormalize by `pk[b,sel]`. Referee: `_leak_sample`
   (bit-level match on a shared `u`).
   TIE-BREAK/GUARD REGISTRY (v2, complete — never "harmonized" silently; serial lines cited):
   `_leak_sample` cumulative `<=` (line 584); Born-stab strict `u < p0` (634); arm-C leak-flag strict
   `u < p2` (623); hard2 strict `u < p1` (781) with `wt <= NUMERICAL_ZERO => p1 = 0.5` (780); hard3
   cumulative STRICT `target < cum` with fallback `kbar=2` (805-812) and `tot <= NUMERICAL_ZERO =>
   kbar=0` (802-803); hard3 `|2>`->bit sub-draw: `gen.random()` if gen else the deterministic residual
   split `u2 = clamp((u - (p0+p1)/tot)/max(p2/tot, NUMERICAL_ZERO), 0, 1)`, `bit = 1 iff u2 <
   b_for_bit` strict (824-833), consumed ONLY when `kbar == 2`; `_renormalize` skips scaling at
   `ns <= NUMERICAL_ZERO` (513-515). Batched implementations realize every guard as a PER-SHOT MASK
   (a degenerate shot must never poison or divide-by-zero the batch).
   v5 FINDING (build review, 2026-07-06): the serial hard3 guard at 802-803 is NaN-SHADOWED DEAD
   CODE in its only reachable regime — `_site_population` (527) is a quimb normalized read that
   divides by trace unconditionally, so an exactly-zero-norm state gives NaN populations, `NaN <=
   NUMERICAL_ZERO` is False, the loop falls through to `kbar=2`, and the sub-draw's NaN-guard
   branches emit `bit=(0.5 < b)`. The BATCHED normative semantics = the WRITTEN guard (`tot <=
   NUMERICAL_ZERO => kbar=0`, per-shot mask, no NaN) — a DECLARED intentional divergence on the
   degenerate regime (class (c) guard); serial-comparison gates fence that regime out and a
   batched-only gate leg covers it; the serial fix is chip task_9f0687fe (serial arm untouched
   in this phase per contract).
   v6 STATUS (2026-07-06, chip task_9f0687fe executed): the serial guard is FIXED —
   `_terminal_readout` reads the level populations only when the pre-read norm
   `wt > NUMERICAL_ZERO` (bit-identical on any live state: the same normalized reads + arithmetic;
   the degenerate leg lands on the written `kbar=0`/`bit=0` path, no NaN). The declared divergence
   is RESOLVED — serial and batched share the degenerate semantics. Gate =
   `tests/test_mps_terminal_degenerate_guard.py` via `outputs/twin_validation/
   hard3_degenerate_guard_run.sh`: the pre-fix RED run reproduced the predicted fall-through
   EXACTLY (levels=[2,2,2,2], bits=[1,1,1,1]; log `logs/hard3_degenerate_guard_prefix_red.log`),
   post-fix 3/3 PASS and the G-OP gates 22/22 re-PASS (live-state serial-referee bit-identity
   holds). The registry's serial line numbers above are the PRE-fix layout (the fix inserts 7
   lines after 799 — the written guard now sits at 809-810). The serial-comparison degenerate
   fence + the batched-only leg can be replaced by a shared-leg gate at the next gate revision
   (not re-run in this chip).
   ARM-C COMPOSITION (v2, normative = serial lines 617-630): per support site SEQUENTIALLY in support
   order — read `p2` = the NORMALIZED 1-site population of the CURRENT (already partially projected)
   state (serial `_site_population`, line 527, `normalized=True`; it coincides with the unnormalized
   read only because the state is renormalized per site — the convention is pinned, not implicit),
   flag strict `u < p2`, project `diag(0,0,1)`/`diag(1,1,0)`, renormalize per site — one uniform per
   site, later sites conditioned on earlier projections, all BEFORE the parity read (normalized).
6. `local_expectation(G[3^w,3^w], sites, normalized=True) -> [B]` — `w <= 4`; NON-CONTIGUOUS support
   handled by IDENTITY-EXTENDED window (G interleaved with `I` on gap sites — exact, class (a));
   window blob `[B, chi_l, 3^w_win, chi_r]` sandwich. LEG ORDER (v2): G's legs correspond to `sites`
   IN THE GIVEN ORDER (the serial/quimb `where` convention); the implementation permutes them
   internally to ascending window order before identity-extension. Referee:
   `_parity_expectation`/`_site_population`.
7. `apply_window_recompress_(G, sites, diagonal: bool) -> (discarded[B], branch_weight[B])` — merge
   the (identity-extended) window into a blob, apply G (diagonal fast path: elementwise scale of the
   3^w axis, guarded by an assert that G's off-diagonal mass is EXACTLY 0 — structural, not floored;
   else matmul). G FORMS (v4, red-team pass 3): shared `[3^w,3^w]`, OR the PER-SHOT DIAGONAL form
   `d[B,3^w]` — the diagonal gather analog of apply_1site_'s `[B,3,3]`, required because the
   Born-stab composition's sqrt(E_s) is a per-shot-VALUED diagonal (sbit sampled per shot; serial
   lines 666-676); off-diagonal assert / center table / discarded[B] / branch_weight[B] semantics
   unchanged; a per-shot NON-diagonal window form is deliberately UNREGISTERED (nothing needs it).
   Re-split LEFT->RIGHT with the v2 SPLIT ROUTING RULE:
   * per split, cap arithmetic decides (class (a), batch-uniform): if `cap_j >= min(m, n_cols)` for
     the split matrix `A[B, m, n_cols]` (no truncation is structurally possible — at EXACT grade this
     holds at EVERY split since `min(m, n_cols) = min(3^(j+1), 3^(n-j-1)) = cap_j`), route **batched
     reduced QR** (backward-stable, no conditioning exposure; discard set structurally EMPTY);
   * else route **Gram + batched-eigh** (hermitize `A A^H`; eigh ascending; keep TOP `cap_j`
     eigenpairs; clamp `max(lambda, 0)` — NEGATIVES-ONLY, no positive floor; zero-pad `U` columns
     beyond the structural rank bound — decided by CAP ARITHMETIC, never a numerical-rank threshold
     on computed lambdas; `M <- U^H A`).
   Renormalize to unit norm internally. `branch_weight` (v2 pinned) = the POST-truncation,
   PRE-renormalization norm^2 (== the serial `nt`, lines 692-694; == `Tr[E_s rho] * <psi|psi>` only
   at exact grade). CENTER TABLE (v2; v3 pins): precondition center canonicalized to the window's
   leftmost site (the op does this itself); postcondition center = the window's RIGHTMOST site.
   Unitary 1-site apply: center unchanged, valid anywhere — the shared `[3,3]` form of apply_1site_
   is REQUIRED unitary (asserted `||U^H U - I||_max <= 1e-12`, class (c) guard); the per-shot
   `[B,3,3]` form is ALWAYS treated as non-unitary (canonicalize to the site first; center = site) —
   the invariant never depends on call-site discipline (v3, red-team). RDM / kraus_sample_: center =
   the site. Multi-site local_expectation (v3 pin): canonicalize to the window's LEFTMOST site
   (matching the window op's precondition); center = that site afterwards.
   Referee: `_apply_sqrt_Es` / codestate `_project`.

### D-3 Discarded-weight book (declared)  [v2]
QR-routed splits (cap arithmetic proves no truncation possible) contribute the LITERAL 0.0 —
structural, DEFINED, never a numerical test on computed lambdas (the batched analog of the serial
`chi >= exact_chi` fast path, lines 679-686; resolves the red-team G-OP-6 blocker: computed
zero-eigenvalues are O(n*eps) floats, a measured book would report ~1e-13, the STRUCTURAL book
reports 0.0). Gram-routed splits contribute their dropped-eigenvalue mass fraction (the Schmidt
identity, class (a) per cut); batched book per op = `1 - prod_j (1 - dropped_j)`. The serial book
measures the same quantity as an end-to-end norm gap vs a full-chi reference apply. The two books
coincide (class (a)) when EXACTLY <= 1 split truncates — G-OP-3 is registered ONLY in that regime;
multi-split truncation equivalence is explicitly OPT2-2/3 STATISTICAL territory, never a book
comparison. v4 note: binding-cap-but-rank-fenced runs (the G-OP-5 chi_lo arm) route Gram and report
O(eps) computed book entries, NOT 0.0 — the structural 0.0 is a QR-ROUTE property (cap arithmetic),
never a "truncation-free" property.

### D-4 Registered gates (the test suite = the gate; predict-before-measure: ALL pass; a miss = finding)  [v2]
- **G-OP-1 (exact, ABSOLUTE elementwise <=1e-12 on unit-norm states):** every op,
  DENSE-reconstruction match vs the serial quimb op, on random states whose Schmidt rank <= chi at
  every cut (no gauge/phase freedom expected; ANY phase discrepancy is a bug and fails the gate).
  v2 scope fences: (a) the WINDOW op's G-OP-1 leg runs at the EXACT grade only (post-gate rank can
  exceed a truncating cap by the operator Schmidt rank of G — both arms would truncate by different
  algorithms; truncating-grade window coverage is G-OP-3's, and this routing is REGISTERED); all
  other ops run at BOTH grades. (b) One case uses a permutation-ASYMMETRIC G on a NON-MONOTONIC
  `sites` tuple (every production operator is permutation-symmetric — a leg-order bug is otherwise
  invisible). (c) One case invokes the window op and kraus_sample_ with the center deliberately FAR
  from the target (certifies the canonicalize-first contract, not just fresh canonical states).
- **G-OP-2 (sampling, exact):** shared `u` stream => IDENTICAL selected branches/bits AND <=1e-12
  post-state match. v3 grade fence (mirrors G-OP-1(a); the Born-stab composition contains the
  sqrt(E_s) window op whose post-gate rank exceeds a truncating cap): the WINDOW-CONTAINING leg
  (Born-stab composition) runs at the EXACT grade only; the truncation-free 1-site compositions
  (kraus_sample_, hard2/hard3 terminal incl. the registry guards, arm-C leak-flag) run at BOTH
  grades. v5 branch-coverage wording: the leak Kraus are Choi-eigh ASCENDING (channels.py
  _super_to_kraus), so the no-jump branch is the LAST index; targeted legs select branches by pk
  MAGNITUDE (argmax = no-jump, plus the second-largest, hittability-asserted as a precondition),
  never by literal index; the serial `fallback K-1` clamp is a defensive fp guard unreachable by
  mid-range `u` — verified by construction (min over an empty hit set), deliberately not exercised
  with real draws. The hard3 degenerate (zero-norm) leg is BATCHED-ONLY per the v5 registry
  finding (serial referee NaN-shadowed there). KNIFE-EDGE GUARD (v2): the harness asserts every drawn comparison has margin
  `|u*tot - cumsum_k| > 1e-9` — generalized (v3) to `|u - p| > 1e-9` for the direct-threshold draws
  (`u < p0`, `u < p1`, `u < p2`, `u2 < b_for_bit`; a one-term cumsum) — and re-draws `u` on
  violation (the two arms compute probabilities via different reduction orders, agreeing to
  ~1e-15..1e-13; a within-margin flip is a REGISTERED non-failure, adjudicated — mirrors OPT2-2's
  "bit-identity DIAGNOSTIC ONLY", never a silent tolerance bump; padded-vs-tight / batch-size
  kernel-selection nondeterminism is absorbed by this margin).
- **G-OP-3 (truncating consistency, class (c) thresholds):** a truncating window apply engineered to
  truncate at EXACTLY ONE declared split (zero truncation at all other cuts — the regime where D-3's
  two books are class-(a) identical), with the REGISTERED spectral gap defined as the ABSOLUTE
  difference between the smallest retained and largest discarded eigenvalue of the NORMALIZED
  (unit-trace) Gram spectrum at that split, gap >= 1e-3 (LAMBDA units, unit-trace spectrum — v4
  inline tag; the conditioning fence below is in SIGMA units), AND a retained-spectrum conditioning fence
  `sigma_min(retained)/sigma_max >= 1e-3` asserted in the harness (the declared validity domain of
  the Gram path; Gram eigenvector error scales ~ eps*lambda_max/gap — the retained SUBSPACE, hence
  the truncated state, is gap-governed, not kappa^2-governed). Criteria: |Δeps| <= 1e-10 (valid at
  the d3 test dims; dim-dependence declared) and post-state overlap deficit
  `1 - |<psi_q|psi_b>|^2 <= 1e-10`. Plus one FLAT-SPECTRUM case with the degenerate block ENTIRELY
  retained (degeneracy straddling the cap is ill-posed for any algorithm — excluded by
  construction and declared). The conditioning fence's ratio is taken in SIGMA units, i.e. on
  `sqrt(lambda)` of the Gram spectrum (v3; a lambda-ratio reading would square the declared
  validity domain). Harness also asserts Gram-path eigh quality per call:
  `||U^H U - I||_max <= 1e-12` and the eigh residual (torch batched-eigh routing is
  version-dependent; OPT2-0 measured throughput only). v5: the eigh-quality witness is a
  harness-level re-derivation at the module's ACTUAL shapes and batching (a batched
  `[B, m, m]` eigh on the same device/dtype — batched and single eigensolves dispatch through
  DIFFERENT cuSOLVER kernels, so an unbatched re-derivation cannot witness the module's path;
  internal factors are not exposed). v5 conditioning-fence scope: the sigma-units fence is
  asserted in EVERY harness whose run Gram-routes a split (the trunc-grade state builders and
  the G-OP-5 chi_lo arm, restricted to the structural rank of the constructed state), not only
  G-OP-3 — an unlucky-seed conditioning drift must fail as a clean PRECONDITION, never as an
  unattributed gate miss. A miss on any criterion is a FINDING to adjudicate, never a silent
  tolerance bump.
- **G-OP-4 (batch independence, <=1e-12):** B heterogeneous states through every batched op ==
  each state alone at B=1; compared at the DENSE-RECONSTRUCTION level (site tensors are
  gauge/dispatch-dependent, the state is not) — no cross-shot leakage (THE batch-correctness gate).
- **G-OP-5 (padding invariance, <=1e-12):** v3 re-registration (the v2 wording was VACUOUS: for any
  `chi >= exact grade` the D-1 cap formula yields byte-identical cap tuples — the gate compared a
  run to itself). The two arms are `chi_lo < exact_chi` (the chi term BINDS at interior cuts — caps
  genuinely differ) vs `chi_hi >= exact_chi`, on an ENGINEERED state whose Schmidt rank — including
  the post-gate rank through every op the gate drives — stays <= the chi_lo caps at every cut, so
  BOTH runs are truncation-free but differently padded: identical dense state + identical sampled
  outcomes is then a legitimate exact expectation (knife-edge guard applies). This is the gate that
  guards the D-1 padding mechanism (junk leakage through padded channels, padded-vs-tight kernels).
- **G-OP-6 (ledger, structural):** exact grade => discarded == 0.0 LITERALLY (the D-3 v2 structural
  book: every split QR-routed, discard set empty by cap arithmetic — `==`, not approx).
- **G-OP-7 (micro-sequence, EXACT grade — v3 pin; it contains sqrt(E_s)):** on a small chain, the
  composed sequence gate -> leak-Kraus -> stabilizer-measure (H, parity read, sqrt(E_s), H back) ->
  terminal readout, driven by ONE shared u-stream, matches the serial arm bit-for-bit (knife-edge
  guard applies) + <=1e-12 in state. (The FULL d3 trajectory / statistical gates are OPT2-2.)

### D-5 Declared bounds / scope fences  [v2]
- Window-blob memory `B * chi_l * 3^w_win * chi_r * 16` bytes: trivial at d3 gates; at d5 production
  the op chunks over B if needed (OPT2-3 concern — declared, not silently deferred).
- v5 (build review): the identity-extended DENSE window operator is a SECOND memory term
  `(3^spread)^2 * 16` bytes with `spread = max(sites)-min(sites)+1` — B-independent, so B-chunking
  cannot bound it, and the serial referee has no analog (quimb nonlocal works on support legs).
  Fenced in-module at `spread <= 8` (ValueError past it); a support-leg / diagonal-fast-path
  `local_expectation` for the parity-read hot path on gapped snake supports is REGISTERED OPT2-2
  territory (the window APPLY's diagonal forms already avoid the dense term).
- LAMBDA-UNITS REGISTRY (red-team A-11; Gram eigenvalues are sigma^2 — NUMERICAL_ZERO=1e-12 in
  lambda units means sigma~1e-6, six orders above the gates): (i) the eigenvalue clamp is
  `max(lambda, 0)` — NEGATIVES-ONLY, no positive floor; (ii) padding/rank decisions are STRUCTURAL
  cap arithmetic, never a numerical-rank threshold on computed lambdas (a threshold rank would also
  be batch-heterogeneous, breaking D-1 fixed shapes and G-OP-4); (iii) `from_dense`'s rank assert is
  a class-(c) CONSTRUCTOR GUARD with its threshold declared in lambda units: dropped-mass fraction
  <= 1e-12 per split (sensitivity sigma ~ 1e-6, documented in the docstring; gate test states carry
  O(1) Schmidt values, far from the boundary).
- Gram-path validity domain: retained-spectrum conditioning `sigma_min(retained)/sigma_max >= 1e-3`
  (declared; asserted in gate harnesses; production op streams that leave it are OPT2-2's
  statistical-gate territory).
- No c64 arm, no rank-adaptive shapes, no driver/RunSpec seam in this phase (OPT2-2).

## OPT2-1 OUTCOMES (2026-07-06 gate run — `opt2_1_op_gates_run.sh`, RTX 5090)
- **G-OP-1..7: 22/22 PASS** (log `outputs/twin_validation/logs/opt2_1_op_gates.log`;
  module sha d4fed5d0…, tests sha 328793b2…; 8.2 s GPU). The registered ALL-pass
  prediction HELD for the module: every equivalence/sampling/ledger criterion at both
  chi grades, no knife-edge re-draws adjudicated, discarded == 0.0 literal at exact grade.
- **One registered miss, HARNESS-side (a finding, recorded):** the first run failed both
  G-OP-3 tests inside `_gop3_engineered_case` — the orthonormal families `Au`/`Cu` were
  redrawn PER column j, breaking the staggered-pairing orthogonality the phi'_j design
  rests on (generic overlap ~0.25); the harness's own anti-vacuous QR-pin assert caught
  it before any referee comparison (the assert-your-preconditions pattern paying off).
  Fix: hoist the families out of the loop + a unit-trace assert on each designed
  spectrum. No module change; re-run green.
- **Build-review findings (8 confirmed / 1 refuted, 3-lens un-led + adversarial verify)
  all resolved pre-run:** trunc-grade state builder rank budget (operator-Schmidt-rank
  9, rebuilt as disjoint blocks), Choi-eigh-ascending branch targeting (weight-ranked
  `_pick_branches`), sigma-conditioning fence wired into every Gram-routing harness,
  batched-eigh dispatch witness at the module's [B,6,6] shapes, hard3 batched-only
  degenerate leg (serial NaN-shadow — chip task_9f0687fe), window-spread fence
  `_MAX_WINDOW_SPREAD=8`, honest collision docstring, CODE_MAP + scalable README.
- Design-contract convergence: 4 adversarial passes, blockers 6 -> 2 -> 1 -> 0, all
  fixes contract-level before any code ran on the GPU.
- NEXT: OPT2-2 (batched trajectory driver @ d3 exact grade, RunSpec/sched/ShotSet
  drop-in seam; statistical gates vs the serial arm; throughput gate >= the anchored
  10-100x band).

## OPT2-2 DESIGN — build contract (2026-07-09, written BEFORE code; theory-first)

**Module:** `src/qec_twin/forward/scalable/batched_mps_forward.py` — a NEW sibling class
`BatchedMpsLeakageForward` composing the OPT2-1 `batched_mps.BatchedMps` op core into the
end-to-end `RunSpec/sched → (ShotSet, MpsTruncationLedger)` seam. The serial arm
`mps_forward.MpsLeakageForward` is the REFEREE and stays UNTOUCHED (same discipline as
OPT2-1's sibling-module rule). Torch/cuda/complex128 only. Tests:
`tests/test_batched_mps_forward.py` (`requires_cuda` + `requires_data`).

**GROUNDED SEAMS (Stage-0 verified 2026-07-09 — the design rests on these, cited by named
convention, not line numbers):**
- The serial trajectory control flow is `MpsLeakageForward._run_trajectory`: per round
  `[PRE-seg: GATE (no draw) / LEAK (1 u each)] → [each stabilizer in schedule order:
  (arm-C only: slen leak-flag u's) + 1 Born u_out] → [POST-seg: transversal Y (no draw)]`,
  then terminal `[n_data u's, engine order q=0..n-1]`. This is the "Section-5 draw order".
- Per-shot RNG derivation (VERIFIED, `MpsLeakageForward.sample`): `rng =
  np.random.default_rng((base_seed, shot))`. The batched arm MUST mirror this per-shot key.
- OPT2-1 supplies every primitive: `apply_1site_` (GATE), `kraus_sample_` (LEAK — the
  `_leak_sample` referee, cumulative `<=`), `site_rdm`, `local_expectation` (parity read),
  `apply_window_recompress_` (the `sqrt(E_s)` blob — the `_apply_sqrt_Es` referee),
  `canonicalize_`/`renormalize_`. OPT2-2 writes NO new op primitive; a discovered gap is a
  contract amendment, not a silent driver-local op.
- ShotSet pack/header + the leak_slices entry-guard/provenance are REUSED verbatim from the
  serial `sample` (`SvSampler.pack_shots`, `cptp_residual`, the `leak_slices_mode`/`_sha256`
  header) so gate harnesses are shared and the record schema is identical.

**REUSED-VERBATIM host seams (independence rule: shared LIBRARY, never a re-derivation of the
referee's blind-spot logic — forbid re-implementing any of these in the driver):**
`SvSampler.{marshal_within_cycle, build_within_cycle_leak, cptp_residual, pack_shots, the
ShotSet header build}`; module `{_qutrit_gate (the gate_table = {SV_GATE_IDS[name]:
_qutrit_gate(name)}), _arm_d2, snake_order_from_coords, attach_layout/_eng_to_mps,
build_codestate, mps_from_statevector (the SV→quimb-MPS lift — the d3 codestate path, red-team
v2 N3), MpsTruncationLedger}`. The driver WALKS the same `marsh` CSR and indexes every op
through `_eng_to_mps` — it does not re-derive geometry, gates, or the leak table. (Snake order
is order-independent at exact grade ⇒ not correctness-load-bearing, but reuse it for χ-efficiency
parity.)

**PRECONDITIONS the builder's gate asserts BEFORE any comparison (red-team v2 — verify, don't
assume):** (i) the d3 arm-A logical is **Z-type** ⇒ `marsh.log_supp_isx` is ALL-ZERO ⇒ the
terminal `x_log` X-logical rotation is EMPTY/dormant at d3 (so the D2-2 x_log clause is a
FORWARD-scope fix, unexercised by the d3 gates — see D2-2 note); (ii) the certified comparison
runs serial and batched on the SAME codestate CONSTRUCTION (N3): at the d3 default the serial arm
is `codestate_mode='auto'` ⇒ `build_codestate` DENSE statevector ⇒ `mps_from_statevector` (NOT
`build_codestate_mps_direct`, a different algorithm whose ~1e-13 rounding would inflate the
G-D2-4 whitelist) — the batched arm lifts the SAME dense codestate → `broadcast_from_quimb`.

**G-D2-0 PRECONDITION — VERIFIED (`opt2_2_d3_spread_check.py`, CPU, git d8d9697, 2026-07-09):**
the OPT2-1 window ops fence `spread = max(mps_site)-min(mps_site)+1 <= _MAX_WINDOW_SPREAD=8`.
The REAL d3 XZZX snake geometry has worst stabilizer spread **6** (≤ 8 ⇒ the D2-2 window-op
route NEVER raises at d3); worst dense window operator `(3^6)^2·16 = 8.5 MB` (shared across
shots, transient), per-shot window blob `B·chi_l·3^6·chi_r·16 ≈ 322 MB @ B=1024` (state ≈ 2.9
GB, P-B3) — feasible on the 32 GB card. Only STABILIZER supports are windowed; the logical flip
is per-qutrit (spread 1). The diagonal fast path (`3^spread·16 B`) is an OPT2-3 throughput lever,
NOT required for d3 feasibility.

### D2-1 Representation + batch invariants (reuse OPT2-1 D-1)
`BatchedMps` state `[B, cap_{k-1}, 3, cap_k]`, zero-padded to fixed caps, orthogonality
`center` tracked. Codestate broadcast (N3-pinned): at the d3 default build the codestate the
SAME way the serial comparison arm does — `build_codestate` DENSE statevector → `mps_from_
statevector` (a quimb MPS), NOT `build_codestate_mps_direct` (a different construction whose
~1e-13 diff would inflate the G-D2-4 whitelist) — then `broadcast_from_quimb(cs, B)` so every
shot starts BYTE-identical to serial. EVERY driver op declares its center pre/postcondition
(the D-2 table): LEAK/Born/terminal 1-site collapses REQUIRE center==site (the driver
canonicalizes, never trusts); the window `sqrt(E_s)` apply canonicalizes to its support.

### D2-2 The trajectory driver (batched mirror of `_run_trajectory`)
The batch axis is **B (shots), NEVER the qutrit/round/op axis** — those stay sequential exactly
as in the referee. Codestate: build ONCE the SAME way as serial (d3 default: `build_codestate`
dense → `mps_from_statevector`, `<S>`/`<L>` asserted; N3) → `broadcast_from_quimb(cs, B)` so
every shot starts BYTE-identical. The driver runs `ceil(N/B)` chunks (D2-4), each chunk a batched
pass over ≤ B shots with the GLOBAL per-shot key. `b_eff =
0.5 if readout_conv=='half' else spec.b`; **the stabilizer weight is `d2 = _arm_d2(spec.arm,
spec.b)` using the RAW `spec.b` (NOT `b_eff` — `b_eff` is TERMINAL-ONLY; the per-site parity
operator is `diag(1,-1,d2)` mapping |0>→+1,|1>→−1,|2>→d2, and `sqrt(E_s)` uses the same `d2`).**
One batched pass over all B shots (NOT a shot loop). Per round r:
1. **PRE-seg** walk the marshalled CSR `[round_op_ptr[2r], round_op_ptr[2r+1])` in order:
   `WC_OP_GATE → apply_1site_(U, site)` (shared `[3,3]`); `WC_OP_LEAK → kraus_sample_(
   leak_by_round[r], site, u[B])` (`u[B]` = the op's per-shot draw vector, D2-4).
2. **Stabilizers** (schedule order): rotate X-supports to Z (`apply_1site_` H); parity read
   `<P>[B]` via `local_expectation(diag(1,-1,d2)^⊗supp, support, normalized=True)` (spread ≤ 6,
   G-D2-0); `p0[b] = ½(1+<P>[b])`; `sbit[b] = 0 if u_out[b] < p0[b] else 1` (STRICT `<` —
   Born-stab, PER-SHOT MASK); **build the per-shot `sqrt(E_s)` diagonal VERBATIM from
   `_apply_sqrt_Es`**: `es = ½(1 + (−1)^{sbit[b]}·∏_q d_levels[t_q])` over the 3^w support trits
   with `d_levels=[1,−1,d2]` and **support[0] = MSB leg order**, then `sqrt(clamp(es, min=0))`
   (negatives-only clamp — class-(c) guard against sqrt-of-NaN); apply the per-shot diagonal via
   `apply_window_recompress_` at `max_bond=chi` (exact grade ⇒ discarded ≡ 0); **fold the [B]
   discarded into the ledger B-fold** (`record_cut` B times per stabilizer — see D2-3 ledger
   pin); rotate X-supports back. Append the B-vector of bits to the round-major record.
3. **POST-seg** walk the CSR `[round_op_ptr[2r+1], round_op_ptr[2r+2])` **exactly like PRE**
   (`WC_OP_GATE → apply_1site_`, `WC_OP_LEAK → kraus_sample_` consuming one `u[B]` as walked).
   Today's d3 POST carries only the transversal Y (no LEAK), but the walk MUST be general — a
   hard-coded "Y, no draws" would desync the RNG stream if a POST LEAK ever appears.
Then **terminal (hard2)**:
- **first rotate the X-type LOGICAL support to Z** (mirrors `_terminal_readout`'s `x_log`
  pre-rotation, NO rotate-back). **DORMANT AT d3 (red-team v2 N2):** the d3 arm-A logical is
  Z-type ⇒ `marsh.log_supp_isx` is all-zero ⇒ `x_log` is EMPTY in BOTH arms, so this clause is a
  FORWARD-scope (d5/X-memory) fix, unexercised by the d3 gates (asserted precondition, GROUNDED
  SEAMS). **Byte-identity caveat when it goes live:** the referee applies `x_log` H at the raw
  ENGINE position used DIRECTLY as the quimb site (`_terminal_readout` passes `log_sites_eng`
  UNMAPPED to `_apply_gate`, unlike the per-q bit loop which maps via `_eng_to_mps`) — likely a
  latent serial snake bug. To preserve G-D2-4 byte-identity the batched arm MUST reproduce the
  referee's EXACT indexing (engine-as-site) rather than the "correct" `_eng_to_mps` mapping, OR
  the serial bug is fixed in lockstep under its own chip. Pin this before x_log unparks.
- **SEQUENTIAL over q** (engine order 0..n-1), collapse-conditioned — vectorize the B axis ONLY,
  NEVER over q (the post-syndrome data qutrits are entangled; reading all q from one pre-collapse
  state draws the flip from the wrong, marginal-independent law): for each q, `w1[B] =
  local_expectation(F1, [site], normalized=False)` with `F1=diag(0,1,b_eff)`, `wt[B]=norm_sq()`;
  `p1[b] = w1[b]/wt[b]` where `wt[b] > NUMERICAL_ZERO` else `0.5` (the driver's OWN per-shot
  `where`-mask — do NOT delegate to `local_expectation(normalized=True)`, whose degenerate branch
  returns ~0, not 0.5); `bit[b] = 1 if u_term_q[b] < p1[b] else 0` (STRICT `<`); collapse the
  per-shot `sqrt(F_bit)` via `apply_1site_([B,3,3])`: `bit=1 → diag(0,1,√b_eff)`, `bit=0 →
  diag(1,0,√(1−b_eff))` (F0 = I−F1, so |2> keeps `√(1−b_eff)`); then `renormalize_()` after each
  collapse (bits are ratio-invariant, but the norm-health witness + the degenerate mask depend on
  it — mirrors `_terminal_readout` line 871).
- Flip[b] = parity(bit over the logical engine support) XOR m. Pack → ShotSet + ledger (schema
  identical to serial).

### D2-3 Tie-break registry OWNED by OPT2-2 (realized as PER-SHOT MASKS; never harmonized)
Cited by named convention (the serial referee is `mps_forward`; the OPT2-1 registry mirrors
the same tags):
- **leak-sample** cumulative `<=`, fallback `K-1` — delegated to `kraus_sample_` (OPT2-1;
  bit-level match on shared `u`).
- **Born-stab** `sbit = 0 iff u_out < p0`, STRICT `<` — driver, per-shot mask.
- **hard2 terminal** `bit = 1 iff u < p1`, STRICT `<`, with `wt ≤ NUMERICAL_ZERO ⇒ p1 = 0.5`
  (the driver's OWN `where`-mask on `w1/wt`, NOT `local_expectation(normalized=True)`).
- **sqrt(E_s) build** `sqrt(clamp(es, min=0))` (negatives-only clamp before sqrt) — driver.
- **renormalize** skip at `ns ≤ NUMERICAL_ZERO` — delegated to OPT2-1 `_scale_center_` mask.
- **DEGENERATE-SHOT DIVERGENCE — declared DEAD-IN-REGIME + delegated (red-team v2 B6/N5).**
  Reachability audit (arm-A/hard2/exact/CPTP): `kraus_sample_` selects a `pk>0` branch (never a
  zero-weight one); Born-stab collapses to `p0` or `1−p0` (>0 for the selected outcome); the
  terminal `sqrt(F_bit)` keeps `|0>`/`|2>` weight (`√(1−b_eff)`). ⇒ **no shot is annihilated on
  the TYPICAL (non-knife-edge) path**; a mask is reachable ONLY at a measure-zero leak knife-edge
  (`|u·tot−cumsum|<ε`, prob `~O(N·K·ε)`), whose shots are whitelisted+adjudicated (D2-4). So the
  masks are exercised only at those whitelisted knife-edges (NOT strictly dead — reconciles the
  D2-4 leak-knife-edge clause). Correctness of the masks is therefore DELEGATED to the OPT2-1
  op-core gates
  (`_scale_center_`/`local_expectation` degenerate branches, `batched_mps` tests) that DID
  exercise them — the driver need not re-certify a reachable path it has none of. Declared
  batched-normative (vs the serial quimb `normalized=True` NaN path): the driver's own
  `wt≤NUMERICAL_ZERO ⇒ p1=0.5` mask + the op-core `ns≤NUMERICAL_ZERO` skip. The **Born-stab `p0`
  degenerate** path is delegated ENTIRELY to OPT2-1's `local_expectation` gate (no driver leg —
  it is unreachable in-regime). The **terminal `p1`** path gets ONE white-box no-NaN smoke
  (G-D2-8) that constructs an artificial zero-norm shot — a robustness check, not a reachable-path
  certification.
- **Ledger folding (schema-parity pin):** the serial ledger calls `record_cut` once PER
  stabilizer PER shot and `record_shot_total` once per shot, so `report()` has
  `n_truncating_ops = N·R·n_stab`, `n_shots = N`. The batched driver, running `ceil(N/B)` chunks
  of `Bc` shots (`Bc = discarded.numel() ≤ B`, the LAST chunk partial — N=1e6 is NOT divisible by
  B=1024), MUST fold by the ACTUAL chunk count `Bc`, NOT a fixed `B` (red-team v3): per stabilizer
  increment `n_truncating_ops += Bc`, `sum += discarded.sum()`, `worst = max(worst,
  discarded.max())`, and `record_shot_total` `Bc` times per chunk. Summed over chunks this
  REPRODUCES the serial `n_truncating_ops = N·R·n_stab`, `n_shots = N` — a fixed-`B` fold
  over-counts the partial last chunk and FAILS G-D2-3.
- **DEFERRED, out of THIS phase (scope fence):** arm-C leak-flag `u < p2` and hard3/soft level
  path. CORRECTED rationale (red-team lens-2): arm-C's draw COUNT is schedule-FIXED (`slen` per
  stab, shot-independent) — the real obstacle is the per-shot CONDITIONAL leak-flag PROJECTION
  chain (each support site projects |2> vs {0,1} and renormalizes, later sites conditioned on
  earlier projections) + the `p2` read on the partially-projected state; hard3/soft additionally
  has a GENUINELY shot-variable `|2>→bit` sub-draw fired only when `kbar==2`. Both unpark as
  OPT2-2b after the arm-A/hard2 core is certified. The driver RAISES `NotImplementedError` on
  `arm != 'A'` or `mode != 'hard2'` (never a silent wrong answer).

### D2-4 Batched RNG (matched physics — bit-identity is a BLOCKING gate, not diagnostic)
**B vs N (chunk loop — red-team v2 blocker N1).** `B` is the MEMORY/throughput chunk (P-B3:
B=1024 ⇒ state ≈ 2.9 GB); `N` is the STATISTICAL sample (G-D2-2: N=1e6). N=1e6 states = ~2.8 TB
⇒ INFEASIBLE in one pass, so the driver runs `ceil(N/B)` chunks of ≤ B shots. **The per-shot key
is GLOBAL, not batch-local:** for a chunk covering global shots `[off, off+Bc)`, `gens[j] =
default_rng((base_seed, off + j))` (`j = 0..Bc-1`) — IDENTICAL to the serial key
`default_rng((base_seed, shot))` at `shot = off+j`. Keying by `b in range(B)` per chunk (the
naive form) makes chunk 2 REUSE streams 0..B-1 ⇒ shots 1024..2047 byte-identical to 0..1023 ⇒
duplicated streams ⇒ marginal variance under-counted ~ceil(N/B)× ⇒ G-D2-2 z massively inflated:
a formula-faithful builder produces WRONG physics. Draw `u[Bc]` at each Section-5 draw-point as
one scalar `gens[j].random()` from EACH per-shot generator, in the SAME draw order (leak →
per-stab Born → terminal). NOT a single shared generator drawing size-B blocks; NOT a permuted
order. CPU draw cost is negligible vs GPU.

**Correction to the §1 OPT2-2 line: bit-identity is a BLOCKING gate (G-D2-4), not diagnostic.**
Rationale: every MARGINAL/schema gate is exchangeability-invariant — it passes a driver with a
WRONG seed, a permuted draw order, a single shared generator, or a shot-permuted/joint-scrambled
record. The ONLY construction that certifies the per-shot key + the Section-5 order + the joint
record structure + the logical flip + the per-round leak index is matched-seed byte-identity vs
serial (exactly OPT2-1 G-OP-2). At d3 exact grade both arms are exact and start from the SAME
codestate, so identical bits → identical collapses → the arms stay fp-synchronized (~1e-13); the
EXPECTED number of knife-edge flips over `N~1e3–1e4` is `~N·K·ε ~ 1e-7` ⇒ **the happy path is
EXACT byte-identity** (whitelist essentially empty).
- **Knife-edge whitelist (pinned):** a shot may legitimately differ ONLY if some drawn comparison
  was within `ε = 1e-9` (OPT2-1 G-OP-2's constant) of its boundary — for a DIRECT threshold
  (`|u − p0|` Born, `|u − p1|` terminal) OR the LEAK CUMULATIVE selection
  (`|u·tot − cumsum_k| < ε`, the `_leak_sample` form — a leak knife-edge, which can also route the
  shot into the declared degenerate divergence, and would false-fail a Born/terminal-only
  whitelist). `|whitelist|` must be `~O(N·K·ε)` (tiny); a diff OUTSIDE it FAILS.
- **Adjudication instrument (pinned — so "knife-edge vs bug" is decidable; red-team v3):** the
  referee ops return only aggregates (`_measure_stabilizer→(sbit,discarded)`,
  `_terminal_readout→(flip,bits,…)`, `_leak_sample→sel`) — NO per-draw `p`. So on ANY diff, a
  committed debug harness INDEPENDENTLY RE-DERIVES the per-draw margin at `B=1` for the diverging
  shot (NOT "logging via the referee"): Born `p0` by rotate-then-`_parity_expectation` on the
  reconstructed pre-measure state, terminal `p1` via `w1/wt`, leak `cumsum_k` via recomputed
  `Tr[K†K ρ]` — classifying each drawn comparison by the ε test (`|u−p|<ε` or `|u·tot−cumsum|<ε`).
  This is a harness-side computation (allowed — it does not touch the compared serial logic; if
  serial per-draw exposure is ever wanted, add it as a class-(a) PURE-ADDITION return under its
  own chip, like `_leak_sample`'s `sel`). The gate HARD-FAILS if the predicate cannot be evaluated
  for a diff (never silently whitelist). The DM law is only the independent MARGINAL cross-check
  (G-D2-2), not the per-shot conditional.
This is G-D2-4 below.

### D2-5 Scope fences (builders may NOT drift past these)
- **d3 EXACT grade only** (`chi ≥ exact_chi`, discarded ≡ 0). d5 / fixed-χ / truncation
  statistics = OPT2-3, OUT.
- **arm A + hard2 terminal** = the certified core (the P2-conjunction / p1c path). arm C,
  hard3, soft = DEFERRED (D2-3), driver raises.
- **No new op primitives** (compose OPT2-1); **serial arm untouched**; **no c64**.
- **Certified-run cell MUST exercise `b_eff ≠ spec.b`** (a NON-vacuity fence for the d2-vs-b_eff
  split, D2-2/B2): the gates run at least one cell with `spec.b ≠ 0.5` AND `readout_conv='half'`
  (so `b_eff=0.5 ≠ spec.b`) — else a builder threading `b_eff` into `_arm_d2` passes invisibly.
  The p1c physical cell (`spec.b=0.9`, `readout_conv='biased_b'` ⇒ `b_eff=0.9=spec.b`) does NOT
  exercise the split on its own; add the `half` cell. **This `half` cell MUST be one of the cells
  compared under G-D2-4 (byte-identity vs serial, raw b) OR G-D2-2 (z vs the DM, raw b)** — NOT
  only under G-D2-3/health or G-D2-6/throughput, else the fence is vacuous (red-team v2).

### D2-6 Registered gates (predict-before-measure: ALL pass; a miss is a finding)
The gate design LESSON from the red-team: marginal/schema gates are exchangeability-invariant
(they certify neither the seed/order nor the joint record). The load-bearing certifier is the
BLOCKING byte-identity gate (G-D2-4); the marginal gate certifies PHYSICS against an INDEPENDENT
oracle (G-D2-2, not vs serial — shared quimb lineage, P-B4).

- **G-D2-0 (a, PRECONDITION — PASSED 2026-07-09).** Worst d3 snake stabilizer spread = 6 ≤ 8
  (`opt2_2_d3_spread_check.py`); the window-op route is valid + feasible at d3. (See GROUNDED
  SEAMS.)
- **G-D2-4 (a, BLOCKING — the central certifier) — matched-seed byte-identity vs SERIAL.** Run
  `R=1`, AND **`R≥3` with ≥3 PAIRWISE-DISTINCT, NON-PERIODIC per-round tables** (ideally the
  actual P2 Θ-fan-out sequence — red-team v2 N4: a two-table `[A,B]` R=2 leg is passed by a
  DEVIOUS periodic index `leak_by_round[r%2]` or `min(r,1)` that byte-matches at R≤2 yet
  mis-feeds the non-periodic per-round tables the downstream P2 CMI/G² consumes; R≥3 with a third
  distinct table breaks any periodic/clamped/reversed/off-by-one index). This leg kills: wrong
  seed, permuted draw order, single shared generator, ANY wrong per-round-leak index, a
  shot-permuted or joint-scrambled record, and any flip-only divergence — all of which pass every
  marginal gate. Pass = the packed syndrome+flip buffer AND `terminal_bits` are byte-identical to
  serial up to the D2-4 pinned knife-edge whitelist (direct `|u−p|<ε` OR leak-cumulative
  `|u·tot−cumsum|<ε`, `ε=1e-9`); `|whitelist| ~ O(N·K·ε)` (expected ~0); a diff OUTSIDE it FAILS,
  adjudicated by the D2-4 B=1 per-draw instrument. The R≥3 leg's tables MUST pass the G-D2-5
  RoundSwap control (below) so the leg is provably non-vacuous. Small-N (`N~1e3–1e4`) suffices.
- **G-D2-2 (a, statistical vs the INDEPENDENT DM oracle) — physics correctness.** Full-9q `R=1`
  arm-A/hard2 batched detector marginals vs the EXACT sequential-null DM law (the
  `p1c_full9q_record_bound.py` machinery — NEVER the isolated `dm_oracle.py` DETECTOR_MARG):
  one-sample `z_j = |p̂_j − p_j^DM| / sqrt(p_j^DM(1−p_j^DM)/N) ≤ Z_GATE` per detector, with the
  Bonferroni-adjusted `Z_GATE` over the `n_stab·R` detector family (registered `N=1e6`, `Z_GATE=4`
  ⇒ family FPR calibrated). The DM law is exact (no seed), so this certifies the PHYSICS
  independent of the serial arm's quimb lineage (P-B4). (This SUPERSEDES the deleted two-arm
  batched-vs-serial z-test, which was statistically invalid on matched-seed PAIRED data —
  red-team lens-2; byte-identity vs serial is now G-D2-4's job.)
- **G-D2-8 (a, WHITE-BOX no-NaN smoke — robustness, not a reachable-path cert).** The terminal
  degenerate path is DEAD-IN-REGIME (D2-3 reachability audit), so this is a robustness smoke:
  construct an artificial zero-norm shot in a small batch and call the driver's terminal step
  WHITE-BOX — assert **`p1=0.5` DIRECTLY** (the internal quantity; a black-box `bit` cannot
  distinguish `p1=0.5` from a buggy `p1=0` when the injected `u≥0.5`, so pin the injected terminal
  `u<0.5` and assert `bit=1` as the black-box fallback) and **no NaN anywhere in the batch state**.
  The Born-stab `p0` degenerate path is NOT given a driver leg (unreachable in-regime; delegated
  to OPT2-1's `local_expectation` gate — D2-3).
- **G-D2-3 (health, NOT correctness) — norm + ledger.** `norm_drift ~ 0`; ledger `report()`
  reproduces serial (`n_truncating_ops = N·R·n_stab`, `n_shots = N` — D2-3 folding pin).
  `discarded ≡ 0` at exact grade is a HEALTH witness only (definitionally 0 for any impl,
  including an inert stub — recompression correctness is exercised via the STATE that G-D2-4
  byte-matches, and at truncating grade is OPT2-3 territory).
- **G-D2-5 (controls, non-optional P-B4) — anti-vacuity.** Each control is DEMONSTRATED to trip
  its gate (else the gate is vacuous): CorruptStab (corrupted support) + Shuffle (permuted
  schedule) MUST break G-D2-2 AND G-D2-4; CorruptLogicalSupport MUST break the flip (in G-D2-4's
  buffer + G-D2-flip); **RoundSwap/RoundReverse/RoundConstant** (permute/freeze the per-round
  leak-table sequence — red-team v2 N4/B5) MUST break G-D2-4's byte-identity buffer, PROVING the
  R≥3 leg's tables are observably non-equivalent (a swapped/frozen index changes the record). A
  control that does NOT trip its gate ⇒ the tables/cell are too similar ⇒ re-pick before relying
  on the leg.
- **G-D2-flip (a, statistical) — the logical flip.** The flip is already inside G-D2-4's
  byte-identity buffer; additionally assert the batched per-shot flip-rate matches the DM
  biased-b reference `z ≤ 4` at `N=1e6` (the flip is the load-bearing PRODUCT; this catches a
  wrong `m`, a mis-mapped `_log_eng_support`, or a terminal collapse on the wrong site — NOT the
  x_log rotation, which is dormant at d3 (Z-logical, D2-2 note); the CorruptLogicalSupport control
  keeps it anti-vacuous).
- **G-D2-6 (b) — throughput.** batched shots/min at `B=1024` vs serial `s/shot`, warmup
  excluded. PASS = **≥ 10× (the OPT2-0 anchored band FLOOR)**; `≥ 50×` is a stretch NOTE, not the
  bar (a correct impl landing at 15–40×, squarely inside the registered 10–100× band, must not
  FAIL — red-team lens-5). Report shots/min + the ratio; a sub-10× result is a finding
  adjudicated against the OPT2-0 recompression-cost model.

### D2-7 Predictions (class (b)/(c), before any run)
- P-D2a: G-D2-2 + G-D2-flip pass (`z ≤ 4` vs the DM oracle at N=1e6, Bonferroni over the
  detector family).
- P-D2b: G-D2-4 byte-identity holds — the batched record equals serial EXCEPT a knife-edge
  whitelist of cardinality `~O(N·K·ε)` (small; each adjudicated), at BOTH R=1 and R≥2 distinct
  tables.
- P-D2c: throughput lands in the OPT2-0 anchored band 10–100× serial (~8–100 ms/shot; the P-B1
  1–5 ms/shot pre-spike optimism is retired). PASS ≥ 10×.
- P-D2d: G-D2-8 degenerate leg — `p1=0.5`, `bit=(u<0.5)`, no NaN, masks fire.
A miss on any = finding, adjudicated, never a silent tolerance bump.

### D2-8 Build org (heavy ⇒ contract-first adversarial pipeline)
Red-team the contract to ZERO blockers (Stage 2). Then disjoint-ownership builders: A =
`batched_mps_forward.py` (the driver); B = `test_batched_mps_forward.py` (the gates, written
against THIS contract, cannot see A). Un-led multi-lens review (correctness/conventions;
numerics/GPU per-shot-mask; vacuity/devious) → adversarial verify each finding → fix → GPU
gates (serial, orchestrator-run). src commit waits for explicit user confirmation.

### OPT2-2 CONTRACT RED-TEAM OUTCOMES (2026-07-09 — converged to ZERO blockers)
Three adversarial passes (Workflow, opus/high, un-led lenses reading the referee + op-core in
full), **blockers 8 → 2 → 0**:
- **Pass 1 (5 lenses):** 8 blockers — terminal x_log rotation omitted (B1); stabilizer `d2`
  raw-`spec.b` vs `b_eff` unpinned (B2); terminal per-q loop must stay sequential (B3);
  seed/draw-order/joint-record certified by nothing — bit-identity was diagnostic-only (B4);
  per-round leak index certified by nothing (B5); annihilation masks dead in the gate regime
  (B6); hard2 `p1` degenerate route (B7); invalid two-arm binomial se on paired data (B8). All
  8 closed as contract edits; `+11` amendments adopted.
- **Pass 2 (3 lenses, closure-refutation + new-blocker hunt):** B2/B3/B7/B8 CLOSED; found **2 NEW
  blockers the pass-1 edits introduced** — per-shot RNG keyed `range(B)` breaks under `N≫B`
  chunking (N1); the R=2 `[A,B]` leg is passed by a periodic index (N4). Both closed
  (global-key chunk loop; R≥3 non-periodic tables + RoundSwap control), plus N2/N3 + B4/B5/B6
  residuals tightened.
- **Pass 3 (2 lenses, round-2 closure + new-blocker):** N1/N2/N3/N4/B2/B6 all CLOSED, **ZERO new
  blockers**; 3 closing amendments (B4 adjudication = independent B=1 re-derivation not
  referee-hook logging; D2-3 "dead code" → "exercised only at whitelisted knife-edges"; ledger
  fold uses the chunk count `Bc`, not `B`).
- **Structural preconditions VERIFIED on-box (CPU, `opt2_2_d3_spread_check.py`):** worst d3 snake
  stabilizer spread **6 ≤ 8** (window-op route valid + feasible); d3 arm-A logical **Z-type**,
  `log_supp_isx=[0,0,0]` ⇒ x_log dormant at d3.
Ready for Stage 3 (disjoint-ownership build) pending user src-confirmation.
