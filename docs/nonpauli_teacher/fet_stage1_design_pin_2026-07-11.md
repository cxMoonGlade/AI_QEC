# Stage-1 design pin (v3) — d3 exact-environment truncation (the FET concept gate + fork)

> **v2 (2026-07-11)** — rewritten after a 4-lens adversarial red-team (23 findings,
> 1 blocker + confirmed spec defects). Changes from v1: (1) the collapse/fork decision
> is now anchored to a **Γ-INDEPENDENT** instrument across the WHOLE χ-sweep (v1's
> single-point G-FID-XCHECK was blind to a *pessimistic-Γ* bug → the blocker); (2)
> Γ certified by **two independent contraction routes** (`Γ_TN` == `Γ_dense`), not a
> scalar norm alone; (3) `G-Γ-HERM` moved to the correct **layer** grouping; (4)
> `G-FET-AGREE` demoted from (a)-exact to a (c) heuristic — M2 (gauge-fix + top-χ) is
> NOT the loopy-environment optimum, and ΔFid(M1−M2) is a fork INPUT, not a STOP; (5)
> the fork is now a **trichotomy** with a multi-edge discriminator; (6) the multi-round
> "mini-WP1'" is demoted to a schedule-approximate BONUS, off the load-bearing path.
>
> **v3 (2026-07-11)** — convergence red-team (0 blockers; v1 blocker confirmed CLOSED).
> One confirmed amendment + one note folded in: (7) M1 is now a **multi-restart best-of
> wrapper** (the bare single-init ALS can lock into a local optimum → inflated
> `env_rank` — the v1 symptom via optimizer non-convexity; tn_qsim's own production
> path uses restarts) + **G-FET-OPT** (cross-seed agreement + `Fid_M1≥Fid_M2` floor)
> certifies M1 optimality, which `G-FID-SWEEP` alone does not; `env_rank` down-classed
> to (b)/(c); (8) G-FET-KAT must run the REAL Γ builders; round-0 `S_A==GF(2)` is a
> mandatory precondition; `fid_dense` (not `S_A(CUT_A)`) is the preservation anchor.
>
> **Context.** The single-wire 2D PEPS crux is RESOLVED (a)-exact: the per-edge bond
> growth (4→16→48) is a truncation-GAUGE artifact; the true bipartition `S_A` is
> BOUNDED (2–4 ebits) — `dense_psi` S_A == independent GF(2) stabilizer entropy to
> 2e-16 at d3 leakage-off. Fix = **environment-aware rank selection** in the carrier
> truncator (the over-count enters at `_policy_cut`'s `kept_target =
> _rank_for_tail(_insertion_spectrum, ε)`, a LOCAL pair-insertion read). **Stage 1** =
> a committed **diagnostic script (NO src mutation)** proving/refuting the concept on
> the d3 EXACT state and resolving the one-shot-vs-iterative fork that sets Stage-2.
> Epistemic classes per `docs/METRICS.md`: **(a) exact**, **(b) prediction band**,
> **(c) gate/decision rule**.

---

## §0 — v4 OPERATIVE INSTRUMENT (READ FIRST; supersedes §1/§3/§4/§5 where they conflict)

**Why v4 (post-first-run, 2026-07-11).** The first leak-off GPU run CONFIRMED the
concept Γ-independently — every round-1 grown bond collapses under the exact single-edge
environment with the state EXACTLY preserved (**B4_6 dim16→env_rank1, overlap 1.0,
`Fid_Γ==fid_dense` to 1e-15; post-trunc `S_A=2.000000==GF(2)` dev≤2e-16**). BUT the
single-edge `env_rank` is **trivially 1 for EVERY edge** — the loop-redundancy fact: in a
loopy PEPS any ONE edge is gauge-reducible to rank 1 given the others at full rank. The
physical entanglement (`S_A=2`, rank-4 cut) lives in the **JOINT** of several edges; you
cannot truncate them all to 1 at once. **So single-edge `env_rank` is NOT the feasibility
instrument.** The feasibility question is the **JOINT/SEQUENTIAL** representation: under a
per-edge environment-optimal truncator applied across the grid and across rounds, does the
**max per-edge bond stay BOUNDED (saturate ~4)** while the state stays faithful?

**CORE INSTRUMENT (load-bearing) = sequential multi-edge FET across rounds** (the promoted
"mini-WP1'"). Carrier in `TruncationPolicy("lossless")` (local cut = no-op, keeps exact
rank) + `d_abort=None`. Per syndrome round, ONE FET **sweep** over all grown grid bonds in
a FIXED order: each bond `e` truncated in-place to its env-optimal rank `= smallest χ with
Fid_Γ(e,χ) ≥ 1−EPS_FID` (`EPS_FID=1e-8`) via the multi-restart M1, using the CURRENT
state's exact Γ (so already-truncated neighbours are reflected). Track
`max_bond_after_sweep` across rounds `1..R` (R=6, cheap at d3).

**Anti-circularity preserved — Γ-INDEPENDENT truncation faithfulness (v4 amendment F9).**
Per-edge rank comes from the EXACT Γ's `Fid_Γ` (Γ exact at d3, two-route + KAT certified), so
per-edge fidelity is trustworthy without a per-edge `dense_psi`. State faithfulness is cross-
checked Γ-INDEPENDENTLY by TWO reads, both from `dense_psi` (exact at d3):
- **PRIMARY (cheap, always) — per-round before/after-sweep overlap:** within round `r`, after
  the stabs grow the bonds (`ψ_pre`) and after the FET sweep (`ψ_post`), `fid_sweep_r =
  |⟨ψ_pre|ψ_post⟩|²`. `ψ_pre`/`ψ_post` are the SAME trajectory point (same syndromes, same
  DD-echo frame) so this is the pure round-`r` truncation error, no frame issue; require
  `≥ 1−δ` (δ=1e-8) each round; cumulative bound `Π_r fid_sweep_r`.
- **GOLD (exact cumulative, feasibility-CAPPED) — paired untruncated same-RNG reference:** a
  second trajectory, SAME RNG (`base_seed`,`fit_seed`), lossless, `d_abort=None`, **NO FET**;
  `fid_cum_r = |⟨ψ_ref_r|ψ_trunc_r⟩|²`. Same RNG reproduces syndromes + DD-echo frame ⇒ exact
  cumulative truncation error; require `≥ 1−DELTA` (DELTA=1e-6). The untruncated reference has
  GROWING representation bonds (that IS the over-count) ⇒ run it only while `max ref bond ≤
  REF_CAP=64`; beyond, record "reference capped at round r" and fall back to the per-round
  product bound. `S_A(ψ_trunc_r)` corroborates (leak-off: == GF(2) baseline).

**CRITICAL: never overlap against the round-0 codestate** — the DD echo makes
`|⟨codestate_0|ψ_r⟩|² ~ 0` even at ZERO truncation error (empirically round-1 = 6e-31,
all-zero syndromes; only a SAME-POINT pairing removes the frame). This isolates FET truncation
error from the carrier's forward faithfulness (separately certified by the d3 gates); if the
per-edge `Fid_Γ` picks corrupt the state, `fid_sweep`/`fid_cum` drop and it is caught.

**FORK (sequential frame; trichotomy):**
- **(1) one-shot SUFFICIENT** — ONE sweep/round keeps `max_bond ≤ BOUND_HI (8)` AND
  saturating (not monotone-growing: `max_bond[R] ≤ max_bond[⌈R/2⌉] + 1`) across R rounds,
  state faithful ⇒ Stage-2 src = env-aware single-sweep-per-round rank selection.
- **(2) iterative REQUIRED** — one sweep does not bound it, but `K≤3` repeated sweeps/round
  (re-forming Γ each pass) converge to bounded + faithful ⇒ Stage-2 = iterative multi-sweep FET.
- **(3) genuine MINIMUM** — even K sweeps don't bound while faithful ⇒ single-wire 2D PEPS
  genuinely needs a growing bond (feasibility concern; re-examine).
- **Predicted (1)** for leak-off (Clifford ⇒ an exact bounded-bond stabilizer PEPS exists;
  tn_qsim bounds every surface-code PEPDO edge to ~4 the same way). A leak-off miss is a
  SUSPECTED BUG first (audit the real-bond `G-FID-SWEEP` + two-route Γ + M1), per §5.

**BOUND criterion (recalibrated (b) band):** bounded ⇔ `max_bond ≤ 8` AND saturating
across rounds. (The old single-edge `env_rank∈[2,6]` band is RETIRED — single-edge env_rank
is trivially ~1, not the fork quantity.)

**SUPPORTING diagnostic (demoted, still recorded):** the single-edge `env_rank` per grown
bond + its `fid_dense`/`S_A` (the first-run 16→1, state-exact result) — kept as EVIDENCE of
the per-edge over-count, NOT a fork read.

**THE LOAD-BEARING ANTI-CIRCULAR CERTIFIER = `G-FID-SWEEP` + `G-Γ-CONSTRUCT` on the REAL d3
bonds (v4.1 correction — the KAT is NOT it).** Run in the SUPPORTING phase over the actual
round-1 grown bonds: `G-Γ-CONSTRUCT` (`Γ_TN == Γ_dense`, two independent contraction routes)
+ `G-FID-SWEEP` (`Fid_Γ(χ) == fid_dense(χ)` ∀χ). This IS anti-circular: `fid_dense` is
Γ-INDEPENDENT (it applies the FET-chosen `(U_χ,V†_χ)` to the actual state and reads the
`dense_psi` overlap), so a shared-Γ convention/reindex bug that picks WRONG directions makes
`Fid_Γ` (high, from the buggy Γ) DISAGREE with `fid_dense` (low, from the real state) ⇒ gap ⇒
CAUGHT. **`harness_ok` gates on these + the round-0 `S_A==GF(2)` precondition — NOT the KAT.**
(Empirically these PASS on the real bonds: `Fid_Γ==fid_dense` to 1e-15, `Γ_TN==Γ_dense`.)

**KAT — DEMOTED to a NON-GATING informational sanity (v4.1 — my v4 tree-KAT design was
wrong).** On a TREE (factorized environment) the insertion-spectrum SVD EQUALS the Schmidt
spectrum, so `bare_rank == env_rank` always — **there is NO over-count on a tree**; a unitary
gauge does not inflate the insertion rank. So a tree bond CANNOT test "recover `r < D`" (that
scenario is intrinsically LOOPY). The KAT therefore only sanity-checks, INFORMATIONALLY: (A) a
tree bond of Schmidt rank `r` ⇒ FET gives `env_rank == r` (no spurious OVER-collapse); (B) the
loopy 2×2 plaquette ⇒ FET gives `env_rank < bare_rank` (loop-redundancy detected). Neither
gates `harness_ok`. The `carrier_svd` M1 seed expects carrier-bond structure ⇒ on a standalone
non-carrier KAT tensor it is INAPPLICABLE and must be SKIPPED silently (the other seeds carry;
not an error). Rationale for demotion: the real-bond `G-FID-SWEEP` above already catches every
shared-Γ/solver bug the KAT was meant to (fid_dense is the Γ-independent ground truth).

`fid_dense` **NORM GUARD**: when the truncated-state norm `≤ 1e-12·‖ψ‖`, `fid_dense=0` (never
`inf`/`nan`); and the **`-inf` instability sentinel is EXCLUDED from the G-FID-SWEEP gap max**
(compare `|Fid_Γ−fid_dense|` only where `Fid_Γ` is finite).

**Sweep-order + per-stab notes (declared (c) approximations).** (F7) Truncating edge A to
rank 1 pushes entanglement onto the others, so per-edge retained ranks — and `max_bond` —
depend on the fixed sweep order; run **≥2 sweep orders per round and report `max_bond` = the
MAX over orders** (conservative). (F6) `run_bonus` truncates once per ROUND over ALL grown
grid bonds, whereas the Stage-2 src truncator (`_policy_cut`) runs per STAB over PATH bonds;
the per-round-batch sweep is a declared CONSERVATIVE proxy (it truncates every bond every
round — MORE aggressively bounding than per-stab), and the run must **measure the within-round
peak exact rank** (verify it stays bounded at d3, not assert ≤48). (leak-on) leak-on
bounded-ness is CONDITIONAL on the carrier's forward faithfulness (certified by the d3 SW0/SW1
gates), not re-derived here; report the FULL `N_traj` distribution and require agreement, no
single-trajectory read.

**G-FET-OPT → INFORMATIONAL** (not a hard gate). The optimality certificate is
`fid_dense(env_rank) ≥ 1−1e-8` (Γ-independent) + the KAT + the `Fid_M1 ≥ Fid_M2 − 1e-9`
floor; the cross-seed spread ≤1e-6 requirement is DROPPED (seeds legitimately disagree below
the true rank; best-of-max + `fid_dense` already certify the optimum).

**Retained from v3 unchanged:** the two-route Γ (`G-Γ-CONSTRUCT`/`G-Γ-NORM`/`G-Γ-HERM`), the
multi-restart M1, `G-FID-SWEEP` (with the sentinel-exclusion fix), the round-0 `S_A==GF(2)`
precondition, both regimes A/B, the scripted-execution + independence discipline, exit codes.

---

---

## 1. THE QUESTION Stage 1 answers (and the trichotomy fork)

**Concept:** on the d3 exact state, does an **environment-optimal** rank selection
(the full exact double-layer environment `Γ`, not the local insertion spectrum)
collapse a grown per-edge bond back toward the true bounded Schmidt rank (~4) while
**preserving the physical state** (`S_A` unchanged, global fidelity ≥ 1−1e-8)?

**Explicit FORK (decision rule, class c) — THREE outcomes, not two:**
- **(1) one-shot SUFFICIENT** — single-edge exact-Γ optimal truncation collapses the
  bond (`env_rank` ≪ `bare_rank`, into the band) in BOTH regimes AND preserves the
  state ⇒ Stage-2 src = **environment-aware one-shot rank selection**.
- **(2) iterative/global REQUIRED** — single-edge does NOT collapse, BUT running the
  **iterative multi-edge sweep** (re-form each edge's Γ after its neighbors truncate;
  the tn_qsim `find_optimal_truncation` loop) DOES collapse the bonds with the state
  preserved ⇒ Stage-2 src = iterative multi-edge FET.
- **(3) GENUINE representation minimum** — neither single-edge NOR the multi-edge
  sweep collapses the bond while preserving the state ⇒ the bond is a real minimum of
  the single-wire 2D PEPS on this geometry (a **physics finding**: single-wire needs
  that bond) — NOT an automatic iterative-Stage-2 mandate; re-examine feasibility.

**Predicted outcome:** (1) in BOTH regimes. Grounding: leakage-off is a Clifford /
stabilizer state, which admits an EXACT bounded-bond PEPS on this geometry, so the
over-count is removable local (SW-S6) gauge redundancy the full single-edge
environment sees; tn_qsim collapses every surface-code PEPDO edge to target dim 4 the
same way. Outcome (3) is essentially excluded for the Clifford regime by that
existence argument; the trichotomy exists so a G-COLLAPSE MISS is diagnosed, not
guessed. A miss is a FINDING that redirects Stage 2, never a silent tolerance bump.

---

## 2. REPRESENTATION + the exact environment `Γ` (the one new primitive)

State: `PepsState` — a quimb `TensorNetwork`, one rank-≤5 site tensor per data qutrit
(physical `k{pos}` dim 3, virtual grid-edge bonds `B{a}_{b}`, `a<b`), `CDTYPE=complex128`
on cuda. `dense_psi(state)` → exact `(3^n,)` vector, position-0-most-significant, `n≤9`
(d3 bridge). d3 = 3×3 grid, 9 sites, 12 grid edges, **4 plaquette loops (LOOPY)** — a
single edge is a virtual index that does NOT disconnect the network; its local
insertion spectrum is NOT a Schmidt spectrum. Facts verified in
`carrier/peps/{state,contraction,trajectory,diagnostics}.py` + `pepo/dynamics.py`.

**`Γ[i,I,j,J]` — the single-bond environment (NEW; two independent construction
routes, both EXACT at d3, asserted EQUAL — this is the anti-circular Γ certification):**

Index convention (matches tn_qsim `prepare_Gamma` output order `[i,I,j,J]`):
`i`=A-ket, `I`=A-bra, `j`=B-ket, `J`=B-bra, all dim `D_e`. For target bond
`e = B{A}_{B}` (the unique shared index of `site_tensor(A)`, `site_tensor(B)`):

- **`Γ_TN` (production route, exact at d3):** mirror `expect_double_layer`'s exact
  branch — for every site `_site_pair(state, pos, op=None, row_tag, open_phys=False)`
  (ket = tensor, bra = `conj` with bonds renamed `nm→nm+"~"` via `_bra_ind`, physical
  legs traced) — then SPLIT `e`: ket `e→i` (A), `e→j` (B); bra `e~→I` (A), `e~→J` (B),
  reindexing the throwaway row-tagged copies only. `TensorNetwork(all).contract(
  output_inds=(i,I,j,J), optimize="auto-hq")`.
- **`Γ_dense` (independent referee route):** an explicit dense contraction of the SAME
  site tensors via a from-scratch `opt_einsum`/`torch.einsum` path (all physical legs
  traced ket·bra, all bonds summed except `e` left open on both layers), sharing NO
  code with `contraction.py`'s boundary-MPS machinery. At d3 (n=9) this is a small
  exact contraction.

**Γ gates (all (a) exact, ASSERTED):**
- **G-Γ-CONSTRUCT** — `‖Γ_TN − Γ_dense‖ ≤ 1e-9·‖Γ‖` elementwise. Two independent
  contractors of the environment agree ⇒ the reindex/contraction is correct. *This is
  the Γ certification v1 lacked.* (Use `Γ_TN` downstream.)
- **G-Γ-NORM** — `einsum("iIiI", Γ) == norm_read(state) == ⟨dense_psi|dense_psi⟩`,
  ≤ 1e-9 rel. (Necessary sanity, not sufficient alone.)
- **G-Γ-HERM** — Hermitian PSD in the **LAYER** grouping: permute `(i,I,j,J)→(i,j,I,J)`,
  reshape `(D_e²,D_e²)` = the Gram `Ψ Ψ†`; assert `‖G−G†‖ ≤ 1e-9·‖G‖` and
  `min eig ≥ −1e-9·‖G‖`. (NOT the by-site `(iI),(jJ)` grouping — that is the
  non-normal transfer matrix reserved for the M2 gauge-fix.)

---

## 3. THE FET truncation + the Γ-INDEPENDENT collapse anchor

Ansatz: insert a rank-χ isometry pair on `e`: `δ_{ee'}` → `M = U V†` (`U: D_e×χ`,
`V†: χ×D_e`). **Truncation directions** come from `Γ` via **M1 = the iterative
full-Γ solver** (`find_optimal_truncation_by_Gamma`, reader-extracted, (a)-exact
algebra): half-sweep A `P = einsum("iIjJ,ij,IP->PJ", Γ, I, conj(U))`,
`B = einsum("iIjJ,ip,IP->PJpj", Γ, U, conj(U))` reshaped `(χD_e,χD_e)`,
`Rmax = pinv(B)@P`, `Fid_Γ = P†·Rmax`; symmetric half-sweep B; converge on `|ΔFid|<1e-8`
(≤20 sweeps). M1 optimizes against the FULL loopy Γ.

**M1 is a MULTI-RESTART best-of wrapper, NOT the bare single-init inner solver** (the
non-convexity fix). The tn_qsim INNER ALS (`find_optimal_truncation_by_Gamma`) is
single-init (truncated identity) and can lock into a LOCAL optimum that UNDER-shoots
the achievable rank-χ fidelity — inflating `env_rank` with every Γ-gate green (the
v1-blocker symptom via optimizer non-convexity instead of a wrong Γ). tn_qsim's OWN
production path (`calc_optimal_truncation` / `execute_optimal_truncation`) defends with
random-permuted init + fluctuation kicks + a 10× restart loop; we mirror it. At each χ,
run the ALS from ≥4 seeds — (i) truncated identity, (ii) the carrier's own local-SVD
top-χ of `R_A R_B^T`, (iii) the M2 gauge-fixed dominant-eigenbasis, (iv) ≥1 random
isometry (seed varied by χ+edge index, no wall-clock/`random` global) — RESTART on the
instability/no-improvement fallback rather than returning the identity-init verbatim,
and take `Fid_Γ(χ) = max` over seeds with its `(U_χ,V†_χ)`. **`env_rank` derived from
M1 is therefore (b)/(c), NOT (a):** the per-sweep algebra is exact, but the ALS fixed
point is not a proven global optimum.

**THE ANTI-CIRCULAR COLLAPSE ANCHOR (the blocker fix).** For each candidate
`χ = 1,2,…,bare_rank`: build the M1 rank-χ truncation `(U_χ,V†_χ)`, APPLY it to a COPY
of the state, recompute `dense_psi_after`, and measure the **Γ-INDEPENDENT** global
fidelity from the exact states:
`fid_dense(χ) = |⟨dense_psi_before | dense_psi_after(χ)⟩|² / (‖·‖²‖·‖²)`.
Then:
- **`env_rank` is defined from `fid_dense`, NOT from `Γ`:** the smallest χ with
  `fid_dense(χ) ≥ 1 − 1e-8`. (A pessimistic/insufficient Γ that mis-estimates the
  fidelity cannot inflate `env_rank`, because acceptance is judged by the true state
  overlap.)
- **G-FID-SWEEP (a) exact — the load-bearer:** `|Fid_Γ(χ) − fid_dense(χ)| ≤ 1e-6` for
  ALL χ (the whole sweep, not just at `env_rank`). Γ-math and the dense state are
  independent instruments; full-sweep agreement is the genuine anti-circular Γ
  certification and catches over-KEEPING (the v1 blind spot). A miss ⇒ Γ or the
  write-back is wrong ⇒ STOP + fix (harness), NEVER a physics finding.
- **G-FET-OPT (c) — M1 global-optimality certificate (the convergence-red-team fix):**
  `G-FID-SWEEP` certifies Γ, NOT that M1 found the *max-fidelity* rank-χ truncation — a
  stuck single-init ALS scores its own suboptimal insertion self-consistently. So: (i)
  the ≥4 seeds must AGREE on `Fid_Γ(χ)` at each χ to ≤ 1e-6 (cross-seed spread); a
  larger spread ⇒ the ALS is not at the rank-χ global optimum ⇒ STOP (audit the solver),
  NOT a fork datum; (ii) the reinstated FLOOR `Fid_M1(χ) ≥ Fid_M2(χ) − 1e-9` (M1 must
  never do WORSE than the closed-form M2 seed). These certify that `env_rank` reflects
  the ENVIRONMENT optimum, not a solver artifact — the gap the single-init anchor left.

`bare_rank` = the carrier's OWN over-count baseline, read the carrier's way:
`_rank_for_tail(_insertion_spectrum(e), ε=1e-8)` (so the "16 vs ~4" gap is not
manufactured by a different spectrum/ε — devious-lens guard).

**M2 (demoted to (c) heuristic, NOT load-bearing):** the closed-form gauge-fix
(dominant transfer eigenvectors → canonical bond spectrum σ → top-χ). It is the
LOOP-FREE/simple-update approximation and is optimal ONLY at an exactly-lossless gap;
for a loopy Γ `Fid_M1 ≥ Fid_M2`. Recorded for one purpose: **ΔFid(χ) = Fid_M1(χ) −
Fid_M2(χ)** is a FORK INPUT (ΔFid ≈ 0 ⇒ redundancy is loop-local/simple-update-removable
⇒ outcome (1); ΔFid ≫ 0 at `env_rank` ⇒ the full environment matters ⇒ leans (2)).
**G-FET-AGREE is REMOVED from the (a)-exact/STOP roll-up.** M1≠M2 is expected in the
loopy regime and is informative, not a bug.

**G-FET-KAT (a) — FET solver known-answer test (closes the shared-convention residual).**
The truncation DIRECTIONS come from `Γ`; a shared conceptual reindex/convention error
in BOTH Γ routes would pick suboptimal directions (inflating `env_rank`) while passing
`G-Γ-CONSTRUCT`. Guard: a hand-built minimal reference with an ANALYTICALLY-known
environment-optimal rank — (i) a product (no-loop) bond where `env_rank == bare_rank`
(FET must NOT over-collapse), and (ii) a single-plaquette (2×2) PEPS carrying a bond
whose exact environment-optimal rank is known by construction (e.g. a codestate slice
with a hand-set rank-2 cut inflated to bond-4 by a known gauge) where `env_rank` must
recover the constructed rank. The FET/M1 solver + the Γ builder must reproduce both,
independent of the d3 carrier. G-FET-KAT MUST invoke the REAL `Γ_TN` and `Γ_dense`
builders + the multi-restart M1 on the reference states (asserting `Γ_TN==Γ_dense`
there too), NOT a hand-computed Γ — else a shared reindex/convention bug in the
production routes is never exercised and the KAT is vacuous (V2-5). A miss ⇒ FET/Γ math
bug, STOP.

**Write-back:** absorb `U` into A's tensor, `V†` into B's, reconnect the new χ-bond,
mirroring `ntu_truncate`'s write-back layout (`T_A'=QA0·U·√S`, `T_B'=QB0·Vh^T·√S`).
Diagnostic-script-only (NOT src).

**Cost bound (d3):** `Γ` is `D_e⁴·16 B ≤ 85 MB` at `D_e≤48`. The M1 B-block pinv is
`O((χ·D_e)³)`. The χ-sweep runs the **FULL range `χ ≤ bare_rank`** (build FIX 2 — the
v1/v2 `χ ≤ 32` cap was REMOVED: a cap below `bare_rank` leaves a non-collapsing bond at
`env_rank=None`, which the collapse verdict then silently drops as a false collapse;
sweeping to `bare_rank` guarantees `env_rank` is always defined, and a non-collapse
shows as `env_rank≈bare_rank`, caught). Bounded at d3 by `d_abort=40` on the captured
bond dim ⇒ `χ·D_e ≤ ~1600` → ~seconds/pinv. No unbounded cost.

---

## 4. THE TEST PROTOCOL (both regimes, d3 exact)

Build codestate (`build_codestate_peps`, patch `d3_at_q6_7`, m=0) + drive rounds via
`PepsSampler.sample(..., R_n=None, R_x=None, round_hook=hook)` (exact route,
byte-identical to the d3 gates).

**CORE gate — single-round concept test (load-bearing, no hook truncation):** drive to
round 1 under the carrier's OWN `TruncationPolicy("dynamic_eps", eps_spike=1e-8,
W_max=160)` (so grown bonds are the REAL artifact bonds, ~16). Then, POST-hoc on the
round-1 state, for each grown grid bond `e` (`bond_profile` dim > code rank):
1. build `Γ` (both routes, G-Γ-CONSTRUCT/NORM/HERM);
2. `bare_rank`; run the χ-sweep → `Fid_Γ(χ)`, `fid_dense(χ)` (G-FID-SWEEP), `env_rank`;
3. apply the `env_rank` truncation for real; recompute `dense_psi` → `S_A`, overlap vs
   pre-truncation, and (leakage-off) the GF(2) baseline.
This alone resolves the fork (per-bond `env_rank` vs `bare_rank` + state preservation).

**BONUS — mini-WP1' multi-round (schedule-approximate, NON-load-bearing, informational):**
to probe "does the bond stay bounded across rounds 1–3", run the carrier in
`TruncationPolicy("lossless")` (its local cut becomes a no-op ⇒ FET-in-hook is the ONLY
lossy truncator, matching Stage-2's replace-the-local-cut intent) with `d_abort=None`
(so within-round exact-rank growth cannot pre-empt the hook mid-round — d3 grown dims
≤48 are memory-safe). `round_hook` applies the env-optimal truncation to every grown
grid bond after each round. **G-BOUNDED is declared schedule-approximate (per-round
batch, not per-stab) and is NOT in the fork's load-bearing set** — it can only fail if
FET itself fails to collapse (≡ G-COLLAPSE). Reported as context, not evidence.

**Regime A — leakage-OFF (Clifford, WG_L1=0, θ=0):** independent GT = the inline GF(2)
`stabilizer_entropy_SA(generators=sched.stabilizers+sched.logical, n, CUT_A)` (copy
verbatim, no carrier import; EXACT for stabilizer states). `S_A` read = `carrier_SA`
(restrict to `{0,1}^n`), CUT_A=(0,1,2,3). Baseline `S_A = 2.000` ebits. **MANDATORY
precondition (should-fail control):** the round-0 carrier codestate `S_A` == GF(2)
baseline to ≤ 1e-6 — this proves CUT_A and the generator set agree between the two S_A
instruments BEFORE any truncation is measured; a mismatch ⇒ STOP (mis-wired referee).

**Preservation anchor (V2-5):** `fid_dense` (the GLOBAL overlap) is THE load-bearing
state-preservation instrument. `S_A(CUT_A)` is a SECONDARY check: the d3 grid is loopy
and CUT_A crosses only some edges, so `S_A(CUT_A)` alone is blind to damage on a bond
interior to A or B — it can vote "preserved" while a bond was locally corrupted. Only
`fid_dense ≥ 1−1e-8` votes preservation; `S_A` corroborates via the independent GT.

**Regime B — leakage-ON (WG_L1=5e-3, C_L≈0.199, non-Clifford):** `S_A` read =
`carrier_SA_full` (full `3^n`). GF(2) inapplicable; independent anchors = the Γ-free
`fid_dense` sweep + per-op d3-gate faithfulness (SW0/SW1 vs exact QutritDM, inherited).
`|2⟩`-mass ~1e-3 inflates `bare_rank` (→~29); env/fidelity cut should drop it. N_traj=6
(leakage branches stochastically); verdict per-trajectory; report the full distribution
(no cherry-pick — devious-lens guard).

---

## 5. REGISTERED GATES (predict-before-measure; ALL predicted to pass)

| id | class | prediction | tolerance |
|---|---|---|---|
| G-Γ-CONSTRUCT | (a) | `Γ_TN == Γ_dense` (two independent contractors) | ≤ 1e-9 rel |
| G-Γ-NORM | (a) | `einsum("iIiI",Γ) == norm_read == ⟨ψ|ψ⟩` | ≤ 1e-9 rel |
| G-Γ-HERM | (a) | `Γ` layer-grouping `G_{(ij),(IJ)}` Hermitian PSD | min eig ≥ −1e-9·‖G‖ |
| G-FET-KAT | (a) | FET solver recovers known optimal rank on hand-built refs | exact / ≤ 1e-9 |
| G-FID-SWEEP | (a) | `Fid_Γ(χ) == fid_dense(χ)` for ALL χ | ≤ 1e-6 |
| G-FET-OPT | (c) | ≥4-seed M1 agree on `Fid_Γ(χ)`; `Fid_M1 ≥ Fid_M2` | spread ≤ 1e-6 |
| G-COLLAPSE-OFF | (b) | leakoff: `env_rank ≤ 4` while `bare_rank ≥ 16` (r1) | env_rank band [2,6] |
| G-COLLAPSE-ON | (b) | leakon: `env_rank ≤ 6` while `bare_rank ≥ 16` | env_rank band [2,8] |
| G-SA-OFF | (a) | leakoff post-trunc `S_A == GF(2) baseline` = 2.000 | dev ≤ 1e-4 |
| G-SA-ON | (b) | leakon post-trunc `S_A == 2.000` (unchanged) | dev ≤ 1e-2 |
| ΔFid (c) | (c) | fork INPUT `Fid_M1 − Fid_M2` at `env_rank` (loop-local vs global) | informational |
| G-BOUNDED (c) | (c) | mini-WP1' max bond ≤ 8 across rounds 1–3 | informational, non-load-bearing |

**Fork read (uses ONLY the Γ-independent load-bearers):** `env_rank` (dense-anchored)
+ G-SA-* + G-FID-SWEEP. All pass ⇒ outcome (1), Stage-2 = one-shot env-aware rank
selection. Any G-Γ-*/G-FID-SWEEP/G-FET-KAT miss ⇒ Γ/FET-construction bug (harness),
STOP + fix — NEVER a physics finding.

**A leakage-OFF G-COLLAPSE MISS is a SUSPECTED BUG FIRST, not physics.** An exact
bounded-bond stabilizer PEPS provably EXISTS on this geometry (Gottesman–Knill /
stabilizer-PEPS), so a Clifford-regime bond that does NOT collapse under the exact
full environment contradicts a theorem ⇒ audit the two-route Γ (G-Γ-CONSTRUCT) + the
multi-restart M1 (G-FET-OPT cross-seed spread + `Fid_M1≥Fid_M2` floor, on the ACTUAL
grown bond, not just the G-FET-KAT toys) BEFORE any escalation. Only if the bug audit
is clean is a leakage-off miss escalated — and then via the multi-edge sweep: outcome (2) if it
collapses (state preserved), else outcome (3). (For leakage-ON a G-COLLAPSE miss with
clean G-FID-SWEEP goes straight to the multi-edge discriminator.)

---

## 6. FAITHFULNESS ledger (independent-GT + bounded simplifications)

- **Independent GT (rule I):** (i) `Γ_TN` vs `Γ_dense` — two independent contractors;
  (ii) `Fid_Γ(χ)` vs `fid_dense(χ)` — Γ-math vs the exact state, full sweep; (iii)
  leakoff `S_A` vs GF(2) stabilizer entropy (pure algebra, no carrier code). NONE of the
  fork's load-bearers is a check of Γ against itself.
- **Constraint ledger (rule II):** `Γ` norm-recovery == `dense_psi` norm; `Γ` layer-PSD;
  truncation norm-preserving up to recorded discarded weight; `S_A` a physical
  (gauge-free) bipartition, never the per-edge bond; raw `sched.stabilizers/logical`
  read for the GF(2) generators; `bare_rank` read exactly as the carrier reads it.
- **Bounded simplifications (rule III):** d3-only (`dense_psi` n≤9 — a CONCEPT gate; d5
  goes through boundary-MPS cut-open `S_A` in Stage 2). Single fixed cut CUT_A=(0,1,2,3)
  (the crux showed `S_A` cut-robust — declared (c)). χ-sweep runs the FULL range to
  `bare_rank` (the `χ≤32` cap was removed in build FIX 2; bounded by `d_abort=40`).
  M2 is a loop-free approximation used only as ΔFid context (declared (c)).

## 7. SCOPE FENCES (deliberately NOT in Stage 1)

- NO src mutation (Γ builder + FET + write-back live in the diagnostic script).
- NO d5 (Stage 2); NO boundary-MPS approximate Γ (Stage 2 — d3 uses exact Γ, both routes).
- NO WP1' full R=20–40 saturation run (Stage 3); Stage 1 caps at rounds 1–3.
- NO amendment of `peps_singlewire_spike_contract.md` (Stage 3).
- The multi-edge iterative sweep is run ONLY as the CONTINGENT trichotomy discriminator
  (outcome (2)/(3)); it is not the main path (outcome (1) is predicted).

## 8. DISCIPLINE (scripted-execution + independence)

Committed script under `outputs/nonpauli_teacher/` + `_run.sh` (cd repo, env `aiqec`
bin/python, `py_compile`, `sha256sum` sources, `tee`, `exit ${PIPESTATUS[0]}`),
precondition asserts (CUDA, leakage on/off, d3 shape), flushed evidence, `summary.json`,
`if __name__=="__main__": raise SystemExit(main())`. GPU-only, serialize (no concurrent
GPU). Copy `_gf2_rank/_pauli_to_symplectic/stabilizer_entropy_SA` and `carrier_SA{,_full}`
verbatim; the GF(2) referee imports NOTHING from `carrier.peps`. `Γ_dense` and the FET/M1
solver are new, sharing no code with the carrier's `_policy_cut`/`ntu_truncate` arm they
test NOR with `contraction.py`'s boundary machinery (`Γ_TN`).
