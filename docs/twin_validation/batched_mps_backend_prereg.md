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

### D-1 Representation (fixed shapes — the batch-shots invariant)
`BatchedMps`: `n` site tensors, site `k` = `[B, cap_{k-1}, 3, cap_k]` (boundary caps = 1), where
`cap_k = min(3^(k+1), 3^(n-k-1), chi)` for internal cut `k = 0..n-2`. Tensors are ZERO-PADDED to cap
shapes at all times (padded bond channels carry exactly 0 amplitude — the represented state is
unchanged; class (a) identity). Structural fact (assert in code): `cap_k <= 3*cap_{k-1}` and
`cap_{k-1} <= 3*cap_k` always, so reduced batched QR at cap shapes returns exactly cap-shaped factors
— shapes NEVER change during a run (uniform kernels, the Doi batch-shots pattern).
An explicit orthogonality-`center` invariant is tracked: sites `< center` left-isometric, `> center`
right-isometric (up to zero padding); local reads (RDM/expectations) are valid only at/around the
center — every read canonicalizes first (batched QR sweeps; right sweep via QR of the
conjugate-transposed matrix).

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
   (bit-level match on a shared `u`). NOTE the tie-break asymmetry across serial ops: `_leak_sample`
   uses `<=`, the Born/hard2/leak-flag samples use strict `<` — compositions in tests/driver must
   reproduce each op's own convention (registered here so it is never "harmonized" silently).
6. `local_expectation(G[3^w,3^w], sites, normalized=True) -> [B]` — `w <= 4`; NON-CONTIGUOUS support
   handled by IDENTITY-EXTENDED window (G interleaved with `I` on gap sites — exact, class (a));
   window blob `[B, chi_l, 3^w_win, chi_r]` sandwich. Referee: `_parity_expectation`/`_site_population`.
7. `apply_window_recompress_(G, sites, diagonal: bool) -> (discarded[B], branch_weight[B])` — merge
   the (identity-extended) window into a blob, apply G (diagonal fast path: elementwise scale of the
   3^w axis; else matmul), re-split LEFT->RIGHT via **Gram + batched-eigh** (hermitize `A A^H`; eigh
   ascending; keep the TOP `cap` eigenpairs; zero-pad `U` columns if rank < cap; `M <- U^H A`),
   renormalize to unit norm, return per-shot discarded weight + the pre-renormalization norm^2
   (the branch weight callers need). Referee: `_apply_sqrt_Es` / codestate `_project`.

### D-3 Discarded-weight book (declared)
Batched book per op = `1 - prod_j (1 - dropped_mass_fraction at split j)` over the `w-1` splits (each
split's dropped fraction = discarded-eigenvalue mass / total — the Schmidt identity, class (a) per
cut). The serial book measures the SAME quantity as an end-to-end norm gap vs a full-chi reference
apply. The two books coincide when <= 1 split truncates (in particular BOTH are structurally 0 at
exact grade); with multiple truncating splits they are order-dependent per-cut books of the same
class-(a) family — the equivalence gates compare them only in the zero-truncation regime, and the
truncating-case gate (G-OP-3) compares physics (fidelity/overlap), not book internals.

### D-4 Registered gates (the test suite = the gate; predict-before-measure: ALL pass; a miss = finding)
- **G-OP-1 (exact, <=1e-12):** every op, DENSE-reconstruction elementwise match vs the serial quimb
  op, at BOTH chi grades, on random states whose Schmidt rank <= chi (so truncation is structurally
  zero and the op is a deterministic linear map — no gauge/phase freedom is expected; ANY phase
  discrepancy is a bug, not gauge, and fails the gate).
- **G-OP-2 (sampling, exact):** shared `u` stream => IDENTICAL selected branches/bits AND <=1e-12
  post-state match (both grades; covers kraus_sample_, Born-stab composition, hard2/hard3 terminal
  composition, arm-C leak-flag composition).
- **G-OP-3 (truncating consistency, class (c) threshold):** a genuinely truncating window apply on a
  random state with a REGISTERED retained/discarded spectral gap (>=1e-3): arms agree on discarded
  weight to |Δeps| <= 1e-10 and on the post-state overlap `1 - |<psi_q|psi_b>|^2 <= 1e-10`. Rationale
  (class (a) backdrop): the truncated state depends on the retained SUBSPACE, not on individual
  eigenvector rotations, so agreement is governed by the gap, not by Gram's kappa^2. A miss here is a
  FINDING to adjudicate (sequential-split order difference), never a silent tolerance bump.
- **G-OP-4 (batch independence, <=1e-12):** B heterogeneous states through every batched op ==
  each state alone at B=1 (no cross-shot leakage — THE batch-correctness gate).
- **G-OP-5 (padding invariance, <=1e-12):** zero-padded caps vs tight bonds: identical dense state +
  identical sampled outcomes.
- **G-OP-6 (ledger):** exact grade => discarded == 0 exactly (structural).
- **G-OP-7 (micro-sequence):** on a small chain, the composed sequence gate -> leak-Kraus ->
  stabilizer-measure (H, parity read, sqrt(E_s), H back) -> terminal readout, driven by ONE shared
  u-stream, matches the serial arm bit-for-bit + <=1e-12 in state. (The FULL d3 trajectory /
  statistical gates are OPT2-2, not here.)

### D-5 Declared bounds / scope fences
- Window-blob memory `B * chi_l * 3^w_win * chi_r * 16` bytes: trivial at d3 gates; at d5 production
  the op chunks over B if needed (OPT2-3 concern — declared, not silently deferred).
- Gram kappa^2: retained-subspace argument above; the NUMERICAL_ZERO floor applies to eigenvalue
  clamps (`max(lambda, 0)`), never to structural zeros.
- No c64 arm, no rank-adaptive shapes, no driver/RunSpec seam in this phase (OPT2-2).
