# d5-crux (2b-ii) — Stage-0 grounding + build list (2026-07-10)

Grounding for the race to the **WP1 bond-saturation bet** (contract-build Stage 0).
Governing contract: [`peps_singlewire_spike_contract.md`](peps_singlewire_spike_contract.md)
v1.0 REGISTERED (SW7-SW9, WP1/WP2, §6.1-6.4). Every fact below was checked IN SOURCE
by a 5-reader sweep (workflow `wf_ae208cc8-9da`, 2026-07-10). This doc is the builder
brief; outcomes backfill into contract §9 at close.

User-chosen direction (2026-07-10): **race to the d5 crux.** SW4/SW5 (record-level,
serve RUNG-C) and YAQS integration are DEFERRED/opportunistic. GPU-only serial; src
commits need explicit user confirmation.

---

## A. Already BUILT — do NOT rebuild (verified in source)

| Capability | Seam | Note |
|---|---|---|
| §6.1 dynamic-ε policy (FULL, not stubbed) | `TruncationPolicy` / `_policy_precut` / `_policy_cut` / `truncate_path_bonds` / `dynamic_truncate`; `W_MAX_DEFAULT=160`, `D_ABORT_DEFAULT=40` (trajectory.py) | window=min(4·r_dyn, W_max); per-cut TOTAL discard ≤ ε_spike; `window_binding` flag + retry-once + `PRECONDITION` orderly stop |
| D_abort=40 orderly stop, PRE-metric | `sample_stab` raises `BondAbortError(bond,dim,profile=bond_profile)` before `truncate_path_bonds` (trajectory.py:446-455); strict `>` (D=40 processed) | RT3-F6 comparator correct |
| Per-round instruments | `bond_profile(state)->{(p,q):dim}`, `max_bond(state)->int` (diagnostics.py); d-generic, cache-free | the SW8 read instruments |
| Flush seam | `round_hook(state,r)` in `run_trajectory` (trajectory.py:577); `PepsSampler` wraps `round_hook(state,r,shot)` (658-660) | the SW8 per-round flush hangs here |
| NormCache machinery | `NormCache` + `norm_cache(state,R_n,fit_seed)` + `cache=` on every read + `cache_n/cache_x` on `born_read_stab` (contraction.py) | BUILT but NOT threaded — see M1 |
| §6.2 accuracy instruments | `cross_route_q1` (resid_rel=\|q1_caps−q1_norm\|/N), `chib_doubling_delta` (delta_rel=\|M(χ_b)−M(2χ_b)\|/N); wired+ledgered in `sample_stab` | floor-table rows 1-3 |
| eps_l (§6.3-compliant BP) | `eps_l(state,*,bp_tol=1e-10,bp_max_sweeps=500)` (diagnostics.py:248); self-contained (`_bp_fixed_point`/`_site_reduced`/`_loop_eps` — no shared code with contraction) | non-convergence FLAGGED not raised |
| loop_rank_probe (WP1 path-A') | `loop_rank_probe(state,bond,*,n_probe=80,...)` (diagnostics.py:340) | diagnostic only |
| d-generic codestate + TT | `build_codestate_peps(sched,m,device='cuda')` (no literal 9; d5=25 in principle); `stab_tt_singlewire`/`_tt_svd` dim-parametrized | `dense_psi` HARD-asserts n≤9 (NO d5 dense bridge) |
| d5 schedule route (GREEN) | p9 `_parse`: `default_r01_paths`/`default_r10_paths('d5_at_q6_5','X')` → `parse_xzzx_circuit(verify=True)` → `.with_within_cycle_streams(...)` (xzzx_parser.py) — ran green n_data=25 n_stab=24 | patch ships on disk; NO `QEC_TWIN_HW_DATA` gate (hard-coded `DEFAULT_DATASET_ROOT`) |
| SW9 anchor | `StimCliffordAnchor(p_x=0.03,seed=4242)` + `_stim_slice_records(sched,...)` (certify/anchors/stim_clifford.py); d-GENERIC over any `XZZXSchedule` | works on d5 sched, no code change |
| Runner + evidence pattern | `outputs/nonpauli_teacher/peps_spike_gates_d3_run.sh` (PATH export, sha256, junitxml, `exit ${PIPESTATUS[0]}`) + `peps_spike_import_check.py` (`def main()->int`, `[tag]` evidence, flush, `__main__` guard) | mirror for SW7/SW8/SW9 |
| Byte-compare surface | `ShotSet.packed_bytes()` / `to_det_obs()` (sv_sampler.py); `SvSampler` marshalling (`marshal_within_cycle`, `build_within_cycle_leak`, `pack_shots`/`unpack_shots`, `build_header`) | PEPS carrier reuses these |

---

## B. The gaps → build items

| id | item | status | build |
|---|---|---|---|
| **M1** | #1 norm-cache threading | PARTIAL (machinery built, loop threads none) | **SRC** trajectory.py + contraction.py. Thread a per-snapshot `NormCache` through `run_trajectory` → `sample_stab`/`leak_sample`/`terminal_readout` into `born_read_stab(cache_n=,cache_x=)` / `site_rdm(cache=)` / `norm_read(cache=)`; add `cache=` to `cross_route_q1`/`chib_doubling_delta`. **CORRECTNESS:** `NormCache` is mutation-blind → rebuild after EVERY `apply_stab_branch`/`truncate_path_bonds`/`apply_site_op`; the shareable window is N/M/§6.2-reads on ONE unmutated snapshot. **INVARIANT:** cache=None when R_n=None ⇒ d3 gates stay 28/28 byte-identical. |
| **S1** | #4 boundary-vs-exact d3 | PARTIAL (both routes exist; never cross-checked at d3) | SCRIPT (d3, cheap). For a set of ops: `expect_double_layer(state,ops,R_n=χ_b)` [boundary] vs `expect_double_layer(state,ops)` [exact full double-layer] and vs `dense_psi`-based ⟨ψ\|M\|ψ⟩; assert ≤ 1e-10 (d3 floor); pin `fit_seed`; sweep χ_b for convergence. |
| **S2** | #3 eps_l evolved-d3 independent-dense ref | MISSING | SCRIPT. Build an EVOLVED d3 state (`build_codestate_peps` + gates/LEAK/`apply_stab_branch`); call `diagnostics.eps_l(state)`; recompute each of the (d−1)²=4 loops' transfer matrix + eps_l by an INDEPENDENT full-norm-network dense contraction; assert MAX & mean ≤ 1e-10. **INDEPENDENCE (FAITHFULNESS rule I):** must NOT import `diagnostics._bp_fixed_point`/`_site_reduced`/`_loop_eps`. **SUBTLE:** at 3×3 each loop's non-loop neighbors' converged BP messages enter its transfer matrix — a naive 4-node loop product (the 2×2 `_loop_eps_dense_reference`) MISMATCHES; the ref must reproduce the boundary environment from scratch. |
| **S3** | SW7 d5 codestate structural cert | PARTIAL (builder+instruments exist; no d5 dense referee) | SCRIPT (structural-ONLY). `build_codestate_peps(d5_sched,m)`; assert k=2 tensor slice == 0.0 (\|2⟩-mass); per-edge raw dim == 2^(chain multiplicity) (promote `_chain_multiplicity_map` pattern from test_peps_spike.py, d-generic over `layout.plaquette_path` on `sched.stab_paulis()`+logical); ⟨S_g⟩=+1 ∀24 & ⟨Z_L⟩=(−1)^m through the caps path (`expect_site_caps`/`terminal_obs_prob`) with χ_b ESCALATION-to-convergence (until zero-truncation OR consecutive reads move < 1e-10), re-read at the SW8 production χ_b (report the discrepancy as §6.2 data); d-generic H-pattern assertion (SF8 replacement, using `qutrit_gate('H')`). NO dense bridge (dense_psi raises at n=25). |
| **S4** | SW8 bond-saturation runner (**THE CRUX**) | PARTIAL (engine hooks built; runner missing) | SCRIPT/RUNNER. Carrier = `carrier.peps.PepsSampler.sample` (**2D PEPS — NOT `mps_forward`**), driven by the d5 sched (p9 route) + `RunSpec` + SvSampler marshalling. `policy=TruncationPolicy('dynamic_eps',eps_spike=1e-8,W_max=160)`, `R_n=R_x=χ_b`, `d_abort=40`, N_traj=8, R=40 (auto-extend 60). `round_hook` → per-round `bond_profile`+`max_bond` **FLUSH TO DISK every round**. **24-GiB projected-peak VRAM tripwire** (peak = metric ≤ W_max⁴·16 B + live state + 3 transients; formula PRINTED per check; orderly stop). WP1 disjoint-window plateau verdict; WP2 `eps_l` on ALL 8 headline traj at r∈{0,1,2,5,10}; §6.2 4th row (R-sweep p0-movement < 1e-8 pre-run + mid-run r=15). Headline ε=1e-8 arm FIRST, then {1e-6,1e-10}. Per-trajectory checkpoint/resume; per-arm projected-total print. **DEPENDS ON:** M1 (perf), S1 (route trust), S3 (codestate). |
| **S5** | SW9 Clifford-slice vs Stim | MISSING; **opportunistic, non-gating for WP1** | DEFERRED (lowest priority). Needs engine-side `X_ERROR(0.03)` per-round injection hook (op stream handles only `WC_OP_GATE`/`WC_OP_LEAK`) + a runner; must NOT consume SW8 records (R-fence) nor route through the Section-5 RNG stream. |

---

## C. Risks / declared caveats

- **M1 stale-read hazard:** `NormCache` does not track mutation — a naive "build once per round" silently returns stale environments after the first stab's update+truncation. Rebuild per mutation; the §6.2 instruments are themselves uncached (chib_doubling_delta = 3 rebuilds/call) — cache-param them too.
- **S2 independence:** reproduce the boundary environment from scratch; no BP-code reuse (else circular or wrong). Anti-toy FAITHFULNESS rule I.
- **S4 runner-owned nets:** the VRAM tripwire and per-round disk flush are the runner's job (`PepsSampler` writes packed+header ONLY at the end). If omitted, a d5 OOM leaves NO partial bond table — the F-REC-1/RT2 failure the contract guards against.
- **d5 within-cycle stream shape NOT independently certified:** `parse_xzzx_circuit(verify=True)` self-checks are d3-tuned (the 4-distinct-H-pattern check is guarded by `len==9` → no-ops at n=25). The p9 route ran green with `verify=True` and is the registered D6 route, but the d5 within-cycle stream shape is a declared (c) caveat feeding SW7, not an independent cert.
- **d5 route path is hard-coded:** `DEFAULT_DATASET_ROOT` is an absolute constant with no env override; a runner cannot redirect it without passing explicit paths to `parse_xzzx_circuit`.
- **§6.1 additive-vs-compositional ledger gap** in the window-binding regime (declared defensive/unreachable-in-spec; below the W_max boundary precut_discarded==0 so additive == compositional).

---

## D. Sequencing + confirm-gates

**Parallel build (Stage 3):** M1 (src) + S1/S3 (cert scripts) + S2 (eps_l ref) + S4 (runner
skeleton). Builders: static checks + `py_compile` + `--collect-only` ONLY — **NO GPU, NO
pytest run, NO script execution** (serial GPU is orchestrator-owned; user's live desktop).

**Then:** Stage-4 un-led multi-lens review (adversarially verified) → apply confirmed fixes
→ d3 gates (M1 byte-identity 28/28 + S1/S2 d3 green) → **[CONFIRM-GATE 1] commit M1 (src)** →
run S3 (SW7 d5) → **[CONFIRM-GATE 2] launch S4 (heavy GPU, ε=1e-8 arm first)** → WP1/WP2
verdict backfilled into contract §9 + metric/rigor audit + CODE_MAP regen + memory RESUME.
