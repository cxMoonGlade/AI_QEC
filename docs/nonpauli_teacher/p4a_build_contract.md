# P4a SV-MC engine — kernel ↔ host interface contract (build spec)

> The disjoint-ownership boundary for the 3-agent build (K / H / V) + reviewer. Pins the data layout, the
> schedule/Kraus marshalling, the **§1.5 measurement-instrument arms** (load-bearing), the per-shot RNG keying +
> draw order (for the bit-faithful test), the shot I/O, and the host↔kernel call signature. Design rationale is
> in [`p4_sv_mc_engine_design.md`](p4_sv_mc_engine_design.md); this doc is the *interface*, not the rationale.
> **All `src/qec_twin/**` here is commit-gated** (kernel, loader, host, the `qutrit_dm.py` arm additions).

> **Precision amendment (2026-07-13, binding).** The active package host derives precision from
> run purpose: fused within-cycle optimization is c64/`screening_only`; final/certification is
> c128/`c128_candidate`. PEPS/MPS remain c128-only. Physics construction, codestate checks,
> composition, and CPTP checks occur in c128; only checked complex execution tables are cast.
> No tolerance or FET change is authorized by this interface.

---

## 0. Ownership map

| Agent | Owns | Files |
|---|---|---|
| **K** (kernel) | the trajectory MCWF CUDA kernel + loader | `src/qec_twin/forward/kernels/sv_traj_d3.cu`, `…/sv_traj_d3_loader.py`; dev scripts `outputs/teacher_prereg/p4a_kernel_*.py` |
| **H** (host) | the host driver + marshalling + I/O **+ the `qutrit_dm.py` arm additions** (oracle Arms C/B1/B2; A exists) | `src/qec_twin/forward/scalable/sv_sampler.py`, `src/qec_twin/forward/exact/qutrit_dm.py`; dev scripts `outputs/teacher_prereg/p4a_host_*.py` |
| **V** (verify) | the §6/§9 correctness harness + Gate 4/5 scripts | `outputs/teacher_prereg/p4a_verify_*.py`, `…/p4a_gate*.py` |

The kernel is a pure compute boundary: it consumes flat arrays (no Python objects), returns a packed shot buffer.
H owns every `parse_xzzx_circuit` / `leakage_kraus_torch` call and all disk I/O. V never imports the kernel
internals — it tests through H's public API + the DM oracle. **Disjoint files; no agent edits another's. Mainline
(`.cu`, `sv_sampler.py`, `qutrit_dm.py`) is commit-gated — built on disk, never committed by the agents.**

---

## 1. State representation `(a)`

- **State vector** `ψ ∈ ℂ^{3^9}`, `3^9 = 19683` amplitudes. **Index convention = qutrit-0 most-significant trit**
  (matches Phase-1 `apply_local_op`): `idx = Σ_{q=0..8} t_q · 3^{8−q}`, `t_q ∈ {0,1,2}`. This MUST equal the DM
  engine's basis ordering (Agent V asserts it via a fixed-state round-trip).
- **dtype:** the host binds dtype to purpose. `run_purpose="optimization"` uses `complex64`
  only on `FusedWithinCycleSampler` / `sv_traj_d3_wc` and stamps `screening_only`;
  final/certification uses `complex128` and stamps `c128_candidate`. A c64 artifact is never
  promoted by an equivalence threshold; candidate evidence requires a separate frozen c128 replay.
- **No `|2⟩`-truncation:** all 3 levels per data qutrit are carried (leakage is the whole point).

---

## 2. Schedule marshalling (H → kernel) `(a)`

From `parse_xzzx_circuit(circuit_path, sweep_word=…)` → `XZZXSchedule`, H produces fixed
index and execution arrays (the d3 circuit is static — marshalled once, not per shot):

- `n_data = 9`, `n_stab = 8`, `R` (rounds).
- `round_gates[R]`: per round, a list of `(gate_id, site)`. `gate_id ∈ {H, X, Y, S, …}` enumerated in a header
  shared by K+H (`SV_GATE_IDS`). Single-qutrit only in P4a (CZ is compiled into the stabilizer parity, not an
  explicit 2-qutrit gate on data — local-leakage scope).
- `stabs[n_stab]`: per stabilizer, `support[k]` (the data-qutrit indices) + `pauli[k] ∈ {X,Z}` per support site +
  `needs_H` (bool: X-support ⇒ Hadamard-rotate to Z before the diagonal measurement, rotate back after).
- `logical`: `support[]` + `kind ∈ {X,Z}` (the logical observable for the terminal readout).
- `gate_unitaries`: the `3×3` complex matrices for each `gate_id` actually used (qutrit H/X/Y/S — `|2⟩` inert for
  H, per Phase-1 `qutrit_hadamard`). Build and check them in complex128; only after those
  checks may the fused host cast the `(n_gates,3,3)` execution table to complex64.

H asserts `XZZXSchedule.verify` passed and that `stab_paulis()` matches `stabs[]` before marshalling.
All schedule/support/index tensors remain int32. For the c128 ABI, state/operator tensors are
complex128 and `urandom`/`norm_drift` are float64; for the c64 optimization ABI they are
complex64 and float32 respectively. Device/dtype/shape/index guards run before JIT launch.

---

## 3. Leakage Kraus marshalling (H → kernel) `(a)`

- `kraus = leakage_kraus_torch(θ, g_seep, g_heat, device=cuda)` constructs the validated WG
  Lindbladian channel as a complex128 `(n_kraus, 3, 3)` array. H completes composition and
  asserts CPTP residual `< 1e-12` in c128. Only then may the fused optimization host cast this
  execution table to complex64; the physical construction/check artifact remains c128.
- The kernel **Kraus-samples** one branch per data qutrit per round: `k ~ p_k = ‖K_k ψ_sub‖²` (Born, via curand),
  then `ψ ← K_k ψ / √p_k`. (Single-qutrit subsystem apply on the SV; reuse the Phase-1 index logic.)
- `(θ, g_seep, g_heat)` are **registered sweeps**, not pinned (per design §0): H takes them per-run from the
  registered grid (`WG_L1_REGIME` etc.), never a hard-coded headline point.

---

## 4. Measurement-instrument ARMS (the load-bearing spec) `(a)`/`(c)`

Per design **§1.5**: the R>1 instrument is **underdetermined** by the R=1 POVM → a registered bracket of arms,
every `%ΔLER` reported as a sensitivity table across them. **No arm is "the physical instrument"; Arm A is the
default *representative*.**

**All arms are DIAGONAL in the trit-product basis** (Z-parity + diagonal leaked readout; X-supports Hadamard-
rotated first — H is diagonal on `{0,1}`, `|2⟩` inert). So each is an elementwise operation on `ψ[c]`, cheap +
branch-free. Per stabilizer (Z-type after rotation) with support `supp`, define the per-qutrit **parity weight**
`d_q(t)` and the config product `P(c) = ∏_{q∈supp} d_q(t_q) ∈ [−1,1]`, with effects
`E_0[c] = ½(1+P(c))`, `E_1[c] = ½(1−P(c))` (`E_0+E_1 = I`).

`d_q(0) = +1`, `d_q(1) = −1` in **every** arm. The arm is set by **`d_q(2)`** (+ a leak-flag projection for C):

| arm | `d_q(2)` | extra step | shares `E_s`? | `C_L` effect | role |
|---|---|---|---|---|---|
| **A** (default) | `1 − 2b` | — | Phase-1 `E_s` | damped `√b`/readout (physical Bayesian) | headline representative |
| **C** | `1 − 2b` | **leak-flag projection** (below) | = A | `→ 0` (max disturbance) | same-`E_s` disturbance comparator |
| **B1** | `+1` (`\|2⟩`≡`\|0⟩`) | — | different | damped (distinguishes `\|1⟩`/`\|2⟩`) | leaked-**decoupled** model |
| **B2** | `−1` (`\|2⟩`≡`\|1⟩`) | — | different | **preserved** (`\|1⟩`/`\|2⟩` indistinguishable) | coherence **upper bound** |

**Arm A / B1 / B2 — single diagonal step:** sample `s` with `p(s) = Σ_c E_s[c]·|ψ[c]|²`; update
`ψ[c] ← √(E_s[c])·ψ[c]`, renormalize. (This is the existing DM `project_stabilizer` `sqrt_e` multiply on the SV;
B1/B2 differ ONLY in the `d_q(2)` used to build `E_s`.)

**Arm C — two diagonal steps (same outcome marginal as A, maximal leakage-sector disturbance):**
1. **leak-flag projection:** project `ψ` onto a sampled leakage pattern `L ⊆ supp` (which support qutrits are
   `|2⟩`), `p(L) = Σ_{c∈L-consistent} |ψ[c]|²` — collapses `|1⟩`/`|2⟩` and `|0⟩`/`|2⟩` coherence on the support
   (preserves the `{0,1}` computational coherence);
2. then Arm-A's diagonal `√E_s` on the surviving `{0,1}` content. Marginal `p(s)` is identical to A (verified by
   the Gate-4 A↔C R=1 agreement); `C_L → 0`.

**`b` enters ONLY `d_q(2)` for A/C** (a classifier boundary, never the `{0,1}` weights). For B1/B2 the syndrome is
`b`-independent (different leaked coupling). **`b` is a registered sweep** `b ∈ {0.5,…,1.0}` (Gate-3 / ablation 4).

**Terminal readout + logical label (Gate 3):** after round `R`, H/kernel **sample** the transversal data readout
in the logical basis (the same per-qutrit diagonal leaked convention — registered: biased-`b` vs 50/50, declared
+ ablated), compute `logical_parity(data)`, and emit `logical_flip = logical_parity(data) XOR m`. **Never** the
input `m`; **never** an expectation threshold.

**`qutrit_dm.py` parity (oracle):** the DM `project_stabilizer` already realizes Arm A. K+H add `arm ∈
{A,C,B1,B2}` (the `d_q(2)` switch + the C leak-flag projection) so the DM oracle and the SV-MC implement the
**same arm** for Gate 4. Commit-gated.

---

## 5. RNG keying + draw order (bit-faithful) `(c)`/`(a)`

- **Per-shot stream (two modes, ONE draw sequence) — resolved by Agent K:** production = curand Philox
  `curand_init(base_seed ^ (shot_id·0x9E3779B97F4A7C15), subsequence=shot_id, 0)` (the contract left `hash` open).
  Batch/wave layout + resume MUST NOT change a shot's trajectory (verified wave-invariant W=32/7/11). For the
  **bit-faithful test**, an optional `urandom` real array `[N, urandom_stride]` is consumed instead, in the order
  below — engine-agnostic, so V's Python reference reproduces it exactly (do NOT mirror curand's internal stream;
  use the `urandom` path).
- **FIXED draw order (normative — kernel == Python reference; ONE uniform per categorical draw):** per round
  `r = 1..R`: (i) gates (deterministic, no draws); (ii) for `q = 0..8`: one leakage-Kraus draw (uniform →
  cumulative-CDF over `p_k`); (iii) for `stab` in schedule order: A/B1/B2 = one outcome-uniform; **C = `supp_len`
  leak-flag uniforms (supp order) THEN one outcome-uniform**. After round `R`: 9 terminal-readout uniforms
  (`q=0..8`). ⇒ `urandom_stride ≥ R·(9 + Σ_s (supp_len_s + 1)) + 9` for Arm C (`R·(9 + n_stab) + 9` for A/B1/B2).
- **No `Date.now()` / launch-order nondeterminism** (binding, scripted-execution rule).

---

## 6. Shot I/O format (kernel → H → disk) `(a)`

- **Kernel return (resolved by Agent K):** `(out_bits: uint8 [N, out_stride], norm_drift: real [N])`,
  `out_stride = ceil(R·n_stab / 8) + 1`. Syndrome bits = **round-major then stab-order** in the first
  `ceil(R·n_stab/8)` bytes (bit-packed); `logical_flip` = the **trailing byte** (value 0/1, not bit-packed, for
  unambiguous access). `norm_drift[i] = |1−⟨ψ|ψ⟩|` pre-terminal (mean = §7 `mean_norm_drift`). H may repack for
  disk if a tighter layout is wanted.
- Header (H writes alongside): `{n_data, n_stab, R, N, arm, b, readout_conv, θ, g_seep, g_heat, base_seed,
  shot_id_offset, run_purpose, dtype, precision_policy, evidence_eligibility, logical_kind,
  numerical_provenance, git_commit}` — self-describing + reproducible. The precision fields must
  agree with `numerical_provenance.run_binding.precision` or the run fails closed.
- H streams waves to disk (CPU-side I/O allowed; trajectory compute stays on-device — GPU-only rule).

---

## 7. Host ↔ kernel call signature (concretized by Agent K — keyword-only)

```
sv_traj_d3(
  codestate,                      # ℂ^{3^9} device SV = |m>_L (H builds it, §8)
  # schedule (§2) — CSR gates + flat stab arrays:
  round_gptr,                     # int32 [R+1]   CSR row-pointer into the per-round gate lists
  gate_uid, gate_site,            # int32 [G]     gate id + data-qutrit site, concatenated over rounds
  gate_unitaries,                 # ℂ [n_gate,3,3]
  stab_supp_len,                  # int32 [n_stab]
  stab_supp,                      # int32 [n_stab, MAX_SUPP]   support sites
  stab_supp_isx,                  # int32 [n_stab, MAX_SUPP]   1 ⇒ X-support (Hadamard-rotate to Z)
  kraus,                          # ℂ [n_kraus,3,3]   (WG leakage)
  log_supp, log_supp_isx,         # int32 [L]   logical support + X-flag
  # instrument (§4) + scalars:
  arm,                            # 0:A 1:C 2:B1 3:B2
  b, readout_conv,                # readout_conv 0:biased_b 1:half
  logical_m, N, base_seed, shot_id_offset, wave,
  urandom=None,                   # real [N, urandom_stride] OR None (→ curand); §5
  dtype='c128',                   # low-level ABI selector; host derives it from run_purpose
) -> (out_bits uint8 [N, out_stride], norm_drift real [N])   # §6
```

The low-level extension exposes the ABI selector, but the active host never treats it as an
independent scientific knob: only within-cycle optimization may request c64. Final/certification,
PEPS, and MPS reject a c64 purpose/dtype combination.

**Compile-time bounds (asserted host-side):** `MAX_STAB=16, MAX_SUPP=8, MAX_KRAUS=8, MAX_LOG_SUPP=12` (d3 fits with
headroom; bump + recompile for a larger code). H wraps this as `SvSampler.sample(run_spec) -> ShotSet`; V calls
only `SvSampler`. The kernel loops waves of `≤ wave` blocks (from the Gate-5 micro-bench), streaming each wave out
— never allocating the full `N`. `peak_mem`/`accept_rate` are NOT kernel outputs (MCWF has no rejection; Gate-5
reads peak memory via `torch.cuda.max_memory_allocated` host-side). **New file:** `forward/kernels/__init__.py`
(K added it so the package imports — H/V take note).

---

## 8. Codestate prep (H) `(a)`

`|m⟩_L` = the `+1` eigenstate of all stabilizers with logical eigenvalue `m`. H builds it ONCE per run as a
complex128 pure SV (small, one-off): start from `|0…0⟩`, project through the stabilizer group (or extract the
DM ground state's pure factor), set the logical via the logical operator. H asserts `⟨S⟩ = +1` for all
stabilizers and `⟨L⟩ = (-1)^m` to `< 1e-10` in c128 before sampling (reuse the Phase-1
`init_logical` codestate check, SV form). Only a fused optimization run casts the already-checked
codestate to complex64 at the execution boundary.

---

## 9. Oracle interfaces (Agent V) `(a)`/`(b)`

- **Bit-faithful (`(a)`):** a host-pre-generated random stream (the §5 order) consumed identically by a Python
  MCWF reference and the kernel ⇒ trajectory bit-identical to FP round-off (per arm).
- **Distribution vs DM oracle (`(b)`):** small code (3–5 qutrit / 5-site sub-register, R=1–2), `arm`-matched DM
  engine = exact; `TV(SV-MC, DM) ~ C/√N` across `N ∈ {1e3,1e4,1e5}` (Gate 4). The DM oracle MUST use the same
  `arm`.
- **Apply-equivalence (`(a)`, inherited):** gate/Kraus applies reuse the Phase-1 subsystem pattern
  (`check_subsystem_apply_equiv.py`, 1e-16).

---

## 10. Acceptance (Gates, from design §6.5)

- **Gate 1** (instrument) — §4 here pins it (arms A/C/B1/B2 + the bracket-report rule). ✅ in-contract.
- **Gate 2** (P4a scope) — local, no ancilla/transport. ✅
- **Gate 3** (logical label) — §4 terminal-readout sampling. ✅ in-contract.
- **Gate 4** (DM convergence) — §9, arm-matched. Agent V.
- **Gate 5** (throughput micro-bench) — §7 wave size + purpose-bound dtype; before any large
  optimization run. It may select batching/wave geometry but cannot promote c64 to evidence. Agent V.

Every check is a committed script (asserts + printed evidence + flushed + `__main__` guard). Nothing runs at
production `N` until Gates 4–5 print green and the reviewer clears the build.
