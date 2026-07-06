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

## 3. Disciplines
Every phase src needs user commit confirmation; committed scripts + runners (aiqec bin on PATH); GPU serial;
un-led review before every gate run; CODE_MAP regen per src change. TJM prereg stays on file (its registered
tie-or-lose bet unaffected); this doc owns the scaling line.
