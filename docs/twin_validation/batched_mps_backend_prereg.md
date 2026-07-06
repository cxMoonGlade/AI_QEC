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
  grades. KNIFE-EDGE GUARD (v2): the harness asserts every drawn comparison has margin
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
  version-dependent; OPT2-0 measured throughput only). A miss on any criterion is a FINDING to
  adjudicate, never a silent tolerance bump.
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
