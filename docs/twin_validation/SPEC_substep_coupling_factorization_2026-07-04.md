# SPEC — exact coupling-component factorization of the substep channel

**Status:** approved 2026-07-04. Builder implements; independent reviewer audits vs the constraint ledger
(§5) + the byte-identical-records gate (§6). H6: no commit without user approval.

## 1. Goal

Eliminate the per-manifest bottleneck: 8 substeps × (`matrix_exp` + Choi `eigh`) on a **1024×1024**
complex128 (the full 5-qubit window, D=32). Replace each full-window channel build with a build over the
**connected components of the substep's 2-qubit coupling graph**. Measured: the largest component in every
substep is **D=4** (one ZZ-coupled pair); the rest are D=2 single-qubit dephasing. So each 1024×1024 eigh
becomes one 16×16 + a few 4×4 eighs. **Exact, not an approximation.**

## 2. The math (why it is exact)

For a substep, `L = -i[Σ_i H_i, ·] + Σ_k D[c_k]` (column-stacking; `liouvillian_superop`,
joint_lindbladian.py:102). Partition the window's qubits into disjoint blocks `{B_m}` such that **every**
individual operator (each `H_i` and each `c_k`) has its qubit support contained in a single block. Then
`L = Σ_m L_{B_m}`, where `L_{B_m}` acts only on block `B_m` (⊗ identity elsewhere). Disjoint-support
superoperators commute: `[L_{B_m}, L_{B_n}] = 0` for `m≠n`. Therefore

    expm(L) = Π_m expm(L_{B_m}) = ⊗_m E_{B_m}        (exact)

The joint substep channel is the **tensor product** of the per-block channels. Applying it to ρ =
applying each block channel to its own qubits, in any order (they commute). **No full-window Kraus is ever
formed** (that would explode to Π_m k_m operators of size 32×32 — the trap to avoid).

The blocks are the **connected components** of the graph with an edge `(a,b)` whenever some single `H_i`
or `c_k` acts non-trivially on both `a` and `b`. Single-qubit dephasing/drive ⇒ no edge ⇒ singleton block.

## 3. Current architecture (touch points, file:line)

- `assemble_substep_channel(H_list, c_list, dt)` — joint_lindbladian.py:291 → `liouvillian_superop` →
  `_superop_expm` (matrix_exp) → `superop_to_kraus` (Choi eigh). Returns Kraus `(k, D, D)`.
- `_assemble_selection_joint_channel(selection, dt_ns, params, device, static_zz_calibrations)` —
  axis1_channel_evidence.py:461. Builds `ideal_controls` + `primitive_bundle`, assembles
  `H_list = ideal_controls.H_list + primitive_bundle.H_list`, `c_list = primitive_bundle.c_list`, calls
  `assemble_substep_channel`, returns `Axis1AssembledSelectionChannel(kraus, primitive_bundle, ideal_controls)`.
- The apply loop — axis1_record_evidence.py:552–629:
  `for selection in layer: assembled = _assemble_selection_joint_channel(...); rho =
  _apply_channel_to_branches(rho, assembled.kraus, selection.participant, num_qubits)`.
  `selection.participant` = the global qubit indices for window-local indices `0..nq-1`.
- Local apply: `_apply_channel_to_branches(rho, kraus, targets, n)` → `apply_channel_local` →
  auto-routes to the fused CUDA kernel `fused_local_kraus` (carrier/accel.py) on CUDA. **A local kraus on
  a small `targets` subset is already supported** — this is what makes the per-component apply cheap.

## 4. Design

### 4.1 New builder (joint_lindbladian.py)

`assemble_substep_channel_factored(H_list, c_list, dt, *, device="cuda", completion="identity_sink",
choi_eigenvalue_tol=0.0) -> list[tuple[tuple[int,...], Tensor]]`

Returns a list of `(local_qubits, comp_kraus)`:
- `local_qubits`: the window-local qubit indices (subset of `0..nq-1`) of the component, sorted ascending.
- `comp_kraus`: `(k_m, 2^|local_qubits|, 2^|local_qubits|)` complex128 Kraus for that component's channel,
  built by the SAME `liouvillian_superop → matrix_exp → superop_to_kraus` on the restricted operators.

Steps:
1. `nq = log2(D)`. Compute each operator's support via a factorization test (see §4.3).
2. Build the coupling graph + connected components (union-find). Assign each `H_i`/`c_k` to the (unique)
   component whose qubit set contains its support.
3. For each component `B_m` (sorted qubit list): **restrict** each assigned operator to `B_m`'s subspace
   (§4.4), giving small `(2^|B_m|, 2^|B_m|)` operators; build `L_{B_m}` via `liouvillian_superop` on the
   restricted lists (reindexed to local `0..|B_m|-1`), then `matrix_exp` + `superop_to_kraus`. Singletons
   with no operators at all cannot occur (every qubit that appears has ≥1 operator); a qubit with only an
   identity contribution ⇒ trivial channel `[I]` (handle: if a component has no non-identity operators,
   its channel is the 1-Kraus identity — but this should not arise for real substeps; assert).
4. Return the list in ascending-first-qubit order (deterministic).

**Fallback (correctness over speed):** if there is a single component spanning all `nq` qubits, return
`[(tuple(range(nq)), assemble_substep_channel(H_list, c_list, dt, ...))]` — identical to the current path.
Also honor an env flag `QEC_TWIN_NO_FACTORIZE=1` that forces this fallback (for the byte-identical A/B test).

### 4.2 Wire into the frontend

- `Axis1AssembledSelectionChannel`: ADD a field `components: tuple[tuple[tuple[int,...], Tensor], ...]`
  (the factored channel in window-local indices). KEEP `kraus` populated ONLY in the single-component
  fallback (or drop it if no other consumer — the reviewer must grep for every `.kraus` consumer first).
- `_assemble_selection_joint_channel`: call `assemble_substep_channel_factored`, store `components`.
- The apply loop (axis1_record_evidence.py:552–629): replace the single apply with
  ```
  for local_qubits, comp_kraus in assembled.components:
      targets = tuple(selection.participant[q] for q in local_qubits)
      rho = _apply_channel_to_branches(rho, comp_kraus, targets, num_qubits)
  ```
  **CRITICAL:** confirm `selection.participant[q]` is the correct global qubit for window-local index `q`
  (the same indexing the full-window operators use). This mapping is the top correctness risk — verify it
  explicitly (§5.7), do not assume.

### 4.3 Operator support test

`A` (2^nq × 2^nq) acts non-trivially on qubit `q` iff it does NOT factor as `B ⊗ I_q`. Test via the
reshape `A.reshape([2]*2nq)`, row axis `q`, col axis `nq+q`: trivial on `q` iff the `(iq=0,jq=1)` and
`(iq=1,jq=0)` blocks are ~0 AND `(0,0)==(1,1)` (tol `1e-9`, absolute — operators are O(1) but dephasing
`c ~ sqrt(γ)` can be ~0.03, so DO NOT use a relative tol that would miss weak couplings). Support = the set
of non-trivial qubits.

### 4.4 Operator restriction (support ⊆ component C)

Given `A` with `support(A) ⊆ C`, extract `A_C` (`2^|C| × 2^|C|`): permute qubits so `C` is in front, reshape
to `(2^|C|, 2^|rest|, 2^|C|, 2^|rest|)`, take `A_C = A_reshaped[:, 0, :, 0]`. **Guard (mandatory):**
reconstruct `A_C ⊗ I_{2^|rest|}` (un-permuted) and assert `max|reconstruct − A| < 1e-9`; a failure means a
mis-assigned operator (support crosses the component) — raise, never silently proceed.

## 5. Constraint ledger (each item has a falsifying test the reviewer runs)

1. **Exact factorization identity.** For random substeps (Hermitian `H_list` + single- and TWO-qubit `c`),
   the factored channel applied to a random ρ equals the full-window `assemble_substep_channel` applied to
   the same ρ, to `< 1e-12`. Falsify: any substep where they differ.
2. **Two-qubit operators are NOT split.** A substep containing a genuine 2-qubit `c` (or ZZ `H`) on `(a,b)`
   must put `a,b` in the SAME component. Falsify: a 2-qubit-coupled pair landing in different components.
3. **Restriction guard fires on mis-assignment.** Feed an operator whose support crosses a component; the
   `A_C ⊗ I` reconstruction assert must raise. Falsify: silent wrong restriction.
4. **CPTP per component and overall.** Each `comp_kraus` satisfies `Σ K†K = I` to `1e-9`.
5. **Component-size generality.** Works for singleton (D=2), pair (D=4), AND ≥3-qubit (D=8) components — do
   not hard-code D=4. Falsify: a 3-qubit cluster (build one) that errors or is mis-handled.
6. **Fallback equivalence.** `QEC_TWIN_NO_FACTORIZE=1` reproduces the CURRENT records bit-for-bit.
7. **Index mapping.** `selection.participant[q]` ↔ window-local qubit `q` is the SAME convention the
   operators use. Verify by constructing a substep with a KNOWN single-qubit error on a KNOWN qubit and
   confirming the factored path flips the SAME detector as the full-window path. Falsify: a permuted-qubit
   record.
8. **No silent full-window fallback masking a bug.** If factorization yields a single full-window component
   for a substep that SHOULD factor (measured: all 8 factor to D≤4), that is a regression — log/assert the
   component structure matches the measured `[[0,3],[1],[2],[4]]`-type decomposition on the 5q fixture.

## 6. Verification gates (all on the desktop RTX 5090; GPU-serial; committed scripts under outputs/twin_validation/)

- **G-channel:** §5.1 channel-equivalence vs `assemble_substep_channel` (independent reference = the
  existing verified full-window path). Random substeps incl. 2-qubit and 3-qubit couplings.
- **G-records (PRIMARY):** end-to-end. `emit(regime, m=0, N, seed)` with a FIXED seed, factored vs
  `QEC_TWIN_NO_FACTORIZE=1` (current path): `det` and `obs` tables **byte-identical**; manifest
  `probabilities` and `total_probability_residual` equal to `< 1e-12`. This is the go/no-go gate.
- **G-suite:** `conda run -n aiqec python -m pytest -q tests/` — every currently-passing test still passes
  (scope to `tests/`; the factorization must not change any observable behavior).
- **G-speed:** re-profile `emit`; report the new per-manifest time + speedup vs the 1.0s baseline.

## 7. Deliverables (builder, before "done")

1. The code (joint_lindbladian.py factored builder + support/restriction utils; frontend wiring).
2. The constraint ledger §5 realized as committed, `__main__`-guarded scripts with printed PASS/FAIL evidence.
3. The G-records byte-identical result (the primary gate) — printed hashes of det/obs tables both ways.
4. A short bounded-simplification note: the ONLY simplification is the exact tensor-product factorization
   (error bound: machine-zero, since it is an identity); the fallback preserves the exact path. No unbounded
   simplification is permitted.
5. Do NOT commit (H6). Present the diff + the gate evidence for user approval.

## 8. Baseline state (already in the working tree, verified, uncommitted)

`joint_lindbladian.py` already has: vectorized Choi, `_robust_eigh` (GPU→CPU fallback), batched Kraus build,
and `assemble_substep_channels_batched`. Build ON TOP of this state. Verify scripts:
`outputs/twin_validation/{choi_vectorize_verify,superop_kraus_vectorize_verify,batched_substep_channel_verify}.py`.
Desktop env: `source /home/cx/miniconda3/etc/profile.d/conda.sh && conda activate aiqec`. Run emit on the
DESKTOP (spark's GB10 gives residual=1.0 — do not use it).
