# P4a state-vector Monte-Carlo sampling engine — design / pre-registration (CUDA)
#### scope: 9-data-qutrit **LOCAL** Wood–Gambetta leakage MCWF sampler (**P4a**). Ancilla-mediated CZ transport = **P4b** (deferred).

> **Scope / decision brief.** Phase-1 built the **exact density-matrix (DM) engine** for the d3 XZZX qutrit
> teacher — correct, but only good for *exact* small-R floors (the 256-cell enumeration thrashes at full d3).
> **P4a (the multi-round LOCAL-leakage headroom test) samples shots**, not enumerates: at `R>1` the syndrome
> space is `2^(8R)` (R=3 is 2²⁴), so the floor is unreachable exactly and the test is **`%ΔLER` of a strong
> decoder vs the Pauli baseline on SAMPLED `(syndrome-history, logical)` shots**. This registers the engine
> that produces those shots: a **batched state-vector quantum-trajectory Monte-Carlo (MCWF)** in **C/CUDA**
> (user decision 2026-06-20: a highly-fixed, embarrassingly-parallel, monotone loop — Python/torch per-op
> launch overhead is fatal at `10⁶ shots × R × ~26 ops`). The **DM engine is repurposed as the gold
> correctness oracle** (exact at small scale) — so it was not wasted. Predictions tagged
> **(a) exact / (b) prediction-band / (c) heuristic-gate**.
>
> **P4a scope (binding, review 2026-06-20).** This engine tests **local** WG leakage / seepage / persistence /
> multi-round temporal memory / DLM-vs-coherent ablation / leaked-soft-readout — on **9 data qutrits, no
> persistent ancilla**. It does **NOT** test ancilla-mediated transport, CZ leakage hopping, or circuit-level
> leakage backaction — those are **P4b** (17-qutrit / MPS, deferred). Results are scoped to local-leakage
> headroom and must **not** be read as full non-Pauli headroom. Two load-bearing review fixes are pinned below:
> the **measurement INSTRUMENT** (not just the POVM effect — §1.5, grounded before freeze) and the
> **physically-sampled logical label** (not the input `m` — §1).

> **Precision amendment (2026-07-13, binding).** Only the active
> `FusedWithinCycleSampler` / `sv_traj_d3_wc` path uses c64, and only when
> `run_purpose="optimization"`; its artifacts are permanently `screening_only`.
> Final/certification runs use c128 and remain `c128_candidate` until their owning gates pass.
> WG channel/codestate construction, composition, and CPTP checks stay c128; only checked complex
> execution tables are cast afterward. PEPS/MPS remain c128-only. This amendment authorizes no
> tolerance or FET changes and supersedes the old precision-promotion wording below.

---

## 0. Object & why CUDA

| | |
|---|---|
| **Object** | a CUDA engine emitting `N≈10⁶` labeled `(syndrome-history, logical)` shots from the d3 XZZX qutrit teacher at `R∈{3,5,10}` (**P4a-local**: 9 data qutrits, no persistent ancilla), under WG leakage `(θ, g_seep, g_heat)` + the swept-`b` leaked readout (registered sweeps, not pinned defaults) |
| **Method** | **MCWF** (Monte-Carlo wave function): each shot is ONE pure-state trajectory; the leakage channel is **Kraus-sampled** (Born), keeping the state pure; stabilizers are **measured by sampling** one outcome each |
| **Why CUDA** | shots are independent (embarrassingly parallel); `block-per-trajectory`; Python/torch would pay ~10µs × `10⁶·R·26` ≈ tens of minutes in *launch overhead alone* (R=10), before any compute |
| **Carrier** | local leakage ⇒ the persistent state is **9 data qutrits = 3⁹ = 19683 amplitudes** (ancilla measured+reset each round, not in the state); transport ⇒ 17 qutrits (Phase-1b, deferred) |

**MCWF is sign-problem-free + exact in the mean — `(a)`.** For a CPTP channel `{Kₖ}` and pure `|ψ⟩`: sample `k`
with `pₖ = ‖Kₖ|ψ⟩‖² ≥ 0` (Born, non-negative — no sign problem), set `|ψ⟩ ← Kₖ|ψ⟩/√pₖ`. The trajectory ensemble
average **equals** the exact density-matrix evolution (standard MCWF theorem) — so the sampled distribution is
unbiased, converging at `O(1/√N)`. This is the same physics as the DM engine, *unraveled*.

---

## 1. The per-trajectory algorithm `(a)` (the physics — must be bit-faithful)

Per shot (one CUDA block), given logical `m∈{0,1}`, per-block RNG, the parsed schedule, the teacher params:

```
psi  = codestate |m>_L                      # 3^9 complex amplitudes
hist = []
for r in 1..R:
    for (gate, site) in round_gates:        # H/X/Y on data (schedule); CZ->stab parity (compiled)
        apply_gate(psi, gate, site)         # subsystem apply on the state vector (reuse Phase-1 pattern)
    for q in data_qutrits:                  # WG leakage channel, Kraus-SAMPLED (keep pure)
        k = sample_index({ ||K_i psi||^2 }) # Born draw via curand
        psi = K_k psi ; psi /= ||psi||
    for stab in stabilizers:                # measure stabilizer = a registered INSTRUMENT ARM (§1.5 bracket)
        bit, psi = measure_stab_instrument(psi, stab, b, arm)  # arm A=√E_s (default) / C=full-trit / B=transparent
        hist.append(bit)
# final logical label = SAMPLED physical terminal readout, NOT the input m (Gate 3):
data = sample_terminal_readout(psi)         # transversal data measurement (registered leaked convention, §1.5)
emit (hist, logical_parity(data) XOR m)     # the logical FLIP relative to the prepared m
```

This is **the DM engine's leakage physics, but (i) on a state vector and (ii) sampling ONE branch per
channel/measurement instead of enumerating** — so each shot is `O(R · (gates + 9·Kraus + 8·meas))` single-pass,
NO DFS, NO snapshots, NO 256-cell blow-up. The WG leakage channel and the effect `E_s` (the syndrome
*distribution*) are identical to Phase-1; the measurement **INSTRUMENT** (the state update) is registered as a
**bracket per §1.5** — Arm A = the minimal-disturbance `√E_s` (default representative), Arm C = full-trit
(same-`E_s` disturbance comparator), Arm B = leaked-transparent (different coupling model, coherence upper bound).
The instrument is **invisible at the Phase-1 R=1 floor** (state discarded) but **decisive at R>1**; every `%ΔLER`
is reported across the arms.

---

## 1.5 Measurement instrument bracket — the load-bearing axis `(a)`/`(c)` (grounded + corrected 2026-06-20)

**The R=1 POVM does not fix the R>1 instrument.** At R=1 only `P(s)=Tr[E_s ρ]` matters → the post-measurement
state is irrelevant. At R>1 the **state update (the instrument) carries the temporal correlations**, and the same
effect `E_b = M_b^†M_b` admits MANY instruments. The original pseudocode's `ψ ← √E_b ψ` had already *silently
chosen* one (Lüders) — not merely defined an outcome probability. Because P4a's whole signal is temporal memory,
the instrument is **load-bearing**, and **invisible to the R=1 P3 floor**. We therefore **do not freeze a single
uncalibrated instrument as physical truth**; we register a bracket and report instrument-dependence.

**Information–disturbance (why "`|2⟩`-untouched + marginal=`E_s`" is barred).** Any instrument whose syndrome-bit
marginal equals the Phase-1 `E_s` — which weights `|2⟩` by `b` — *necessarily* extracts `|1⟩`-vs-`|2⟩`
information, hence *must* disturb the `|2⟩` population + `C_L`. A "`|2⟩`-untouched **and** marginal=`E_s`"
instrument is **impossible for `b∈(0,1)`**: it would let the simulation *read* the `|2⟩` population into the
outcome while paying no backaction — a new toy. (`b` is a classical IQ-discriminator boundary — McEwen 2102.06131
Fig. S4; Suchara 1410.8562 §3; Pattison 2107.13589 §1.3 — post-processing, not a state knob. So `√E_s` is **not**
an artifact; it is the *minimal-disturbance* valid instrument, and its `C_L` damping + population–bit correlation
are physical Bayesian updating.)

**Three arms — keep the four axes distinct.**
- **Arm A — Lüders `√E_s` (PRIMARY / headline representative).** `M_s = √E_s`, `ψ ← M_s ψ/√p_s`. Same `E_s` as
  Phase-1; a legal, minimal-disturbance ("gentle measurement") instrument needing no invented hidden device
  model. **Honest label: a Phase-1-POVM-compatible minimal-disturbance *representative* instrument — NOT a
  device-calibrated truth.**
- **Arm C — full-trit / maximally-dephasing (SAME-`E_s` disturbance comparator).** Resolve `|0⟩,|1⟩,|2⟩` then
  classify by `b`: the *same outcome marginal `E_s`* as A, but a stronger measurement of the leakage sector →
  stronger `C_L` dephasing. **A vs C = same POVM, different backaction** — isolates whether instrument disturbance
  (at fixed R=1 POVM) moves the P4 conclusion.
- **Arm B — transparent leaked-state model (DIFFERENT coupling model; coherence upper bound).** The leaked qutrit
  does **not** participate in per-round syndrome readout (no per-round `b`-coupling — that coupling is the deferred
  ancilla physics); `|2⟩` population + `C_L` pass through untouched; `b` enters only at terminal readout. **This
  does NOT share Phase-1 `E_s`** (Suchara Eqs. 6–8; Fowler 1308.6642 rule 4 "leaked qubit invisible to the
  stabilizer machinery") → it is **not** a same-POVM instrument of A, but a distinct leaked-coupling model,
  reported separately as the **no-coupling / coherence upper bound**.

The four axes that **must not be conflated:**

| axis | comparison | isolates |
|---|---|---|
| primary | Arm A | the headline representative readout |
| same-POVM disturbance | A vs C | instrument backaction at fixed `E_s` |
| leaked-coupling | B vs A/C | whether leakage couples to the per-round syndrome at all |
| channel coherence | coherent WG vs DLM (matched `L₁,L₂`, `C_L=0`) | the *channel*'s coherence, independent of the instrument |

**Guardrail (no over-claim).** We do **not** assert the bracket *contains the physical value regardless* — no
theorem bounds all device instruments by these arms. The honest statement: **the bracket spans the two
physically-relevant extremes for P4a — a Phase-1-compatible minimal-disturbance readout (A/C) and a transparent
no-coupling readout (B). A robust conclusion is one stable across the bracket; otherwise the result is
instrument-model dependent, scoped to its arm, and never promoted as device-robust.** Every P4a `%ΔLER` is
reported as an **interval / sensitivity table across the arms.** The exact Kraus per arm (over mixed `{0,1}`/`|2⟩`
amplitudes) is pinned in the interface contract and **certified by Gate 4** (SV-MC and the DM oracle implement the
*same* arm → must converge at `O(1/√N)`).

**Logical label (Gate 3): sampled, physical.** `logical_flip = logical_parity(sample_terminal_readout(ψ)) XOR m`
— terminal readout **sampled** (registered leaked convention: biased-`b` vs the current 50/50 split — declared +
ablated, Suchara Eqs. 6–8), never the input `m`, never an expectation threshold (else the "truth-to-invert" /
perfect-artifact failure mode returns).

**Registered checks (per axis).**
1. **Same-POVM positive control + disturbance bracket:** A and C **agree at R=1** (shared `E_s`); the R>1 `%ΔLER`
   A↔C spread is the *reported* same-POVM instrument-dependence.
2. **Leaked-coupling:** B's R=1 floor *differs* from A/C (different `E_s`) — that difference is itself the
   per-round leaked-coupling signal; the R>1 B-vs-A/C spread bounds the coherence-preserving extreme.
3. **Leakage-off null:** `θ=g_seep=g_heat=0` ⇒ all three arms coincide + non-local `p̄_{t,t'>1}≈0`.
4. **`b`-flatness at R=1 (Arm A):** tight floor over `b∈{0.5,…,1}`.
5. **Channel coherence (separate axis):** coherent WG vs DLM projection at matched `(L₁,L₂)`, `C_L=0` — held at a
   *fixed* instrument arm so it does not mix with the instrument axes.
6. **`L₂`-monotonicity:** temporal-correlation length + R>1 `%ΔLER` decrease monotonically with seepage `L₂`.

---

## 2. Feasibility / throughput `(a)` byte-count + `(b)` rate

- **State size:** `3⁹ = 19683` amplitudes → **315 KB** (complex128) / **157 KB** (complex64).
- **Batching:** one trajectory per block, **launched in many waves — NOT `10⁴`-resident.** At 157 KB shared/block
  the 5090's ≤228 KB shared/SM admits only ~1 block/SM resident (occupancy is shared-memory-bound), so throughput
  is **wave-limited and MEASURED, never assumed a-priori** (Gate 5 micro-bench pins shots/s). complex128 in
  *global* (315 KB, no shared pressure) trades memory bandwidth for occupancy — the micro-bench picks the winner.
  **Precision is purpose-bound:** optimization uses complex64 only on the active fused within-cycle
  path and is screening-only; final/certification uses complex128 and is only an evidence candidate.
  A comparison with c128 may diagnose a screening run, but cannot promote its c64 artifact.
- **Throughput target `(b)`:** with no per-op launch overhead, `10⁶` shots × R=10 should be **minutes**, not the
  Python-launch hours. A committed micro-benchmark pins shots/s before the production run (the Phase-1 sampling-
  budget §2.5 applies: `N=10⁶` per `(basis, R, regime)`, CI half-width ≲1% at the GO threshold).

---

## 3. CUDA architecture `(c)` design

- **`block-per-trajectory`**: the block's threads cooperate on the 19683-amplitude state vector. Each single-qutrit
  apply is a strided subsystem contraction over the amplitudes (the Phase-1 `apply_local_op` index logic, ported to
  a kernel); each Born weight / norm is a **block reduction**.
- **RNG (per-shot deterministic stream):** each shot's stream is keyed by `seed = hash(base_seed, shot_id)` —
  **to the global shot index, NOT launch order or batch layout** — so the same `shot_id` reproduces the same
  trajectory under any batching/resume. For the §4.1 **bit-faithful** unit test, Python and the kernel consume a
  **host-pre-generated random stream** (the SAME draws in the same order); curand-vs-numpy consumption order would
  otherwise make bit-exactness untestable. Production uses curand keyed by `hash(base_seed, shot_id)`.
- **Specialized circuit:** the d3 XZZX schedule (8 stabilizers, the gate list, the logical) is **fixed** → passed
  once to the kernel (constant/global), not rebuilt per shot. The WG leakage Kraus `(r,3,3)` and `b` are kernel
  inputs.
- **Host driver:** parse the circuit (reuse `parse_xzzx_circuit`), build the leakage Kraus (reuse
  `leakage_kraus`), prepare the codestate, launch the wave loop, collect `(hist, logical)` shots, stream to disk.
- **GPU-only model compute** (binding): the trajectory evolution is on-device; only file streaming is host-side.

---

## 4. Correctness oracle — the certification ladder `(a)`/`(b)` (no over-claim)

The SV-MC is **not** "exact"; it is an **unbiased sampler** certified by a ladder (mirrors §2.6).
Only a c128 final/certification artifact may enter this ladder; a c64 optimization artifact remains
screening-only even if a separate replay agrees:

1. **`(a)` single-trajectory bit-faithful:** a fixed-seed trajectory == an independent Python MCWF reference
   (same Kraus draws, same projections) to FP round-off — proves the kernel implements the algorithm.
2. **`(a)`/`(b)` distribution vs the DM oracle (small scale):** on a **small code** where the DM engine
   enumerates exactly (toy 3–5 qutrit / the 5-site sub-register, R=1–2), the SV-MC's sampled syndrome distribution
   converges to the DM **exact** distribution at **`O(1/√N)`** (TV decreasing as `~1/√N`, within the sampling CI).
   This is the load-bearing certification — the DM engine is the gold oracle here. **Both engines must implement
   the §1.5 arms:** the DM `project_stabilizer` already realizes Arm A (`√E_s`); Arms C (full-trit) and B
   (transparent) are added as the bracket's other arms (a `qutrit_dm.py` change, commit-gated). At R=1 Arms A and
   C share the floor (unchanged); Arm B's R=1 floor *differs* (different `E_s`).
3. **`(a)` apply-equivalence (inherited):** the gate/channel applies reuse the Phase-1 subsystem/superoperator
   pattern, already proven equivalent to the dense reference (`check_subsystem_apply_equiv.py`, 1e-16).
4. **`(b)` cross-method (later):** at full d3 R>1 (no exact oracle), agreement vs the MPS-trajectory (2308.08186)
   corroborates.

**Honest status:** at full d3 R>1 there is **no exact oracle** (the whole reason for sampling); validity rests on
the ladder (1)+(2)+(3) at small scale + the MCWF-exactness theorem + `O(1/√N)` convergence — stated as such, never
"exact at full scale."

---

## 5. Reuse (NOT rebuilt) vs BUILD

**REUSE:** `parse_xzzx_circuit` (schedule), `leakage_kraus`/`leakage_kraus_torch` (the WG channel — validated),
the swept-`b` `E_s` POVM form, the teacher params, the Phase-1 `apply_local_op` index convention (qutrit 0 = MSF),
the DM engine (as the small-scale oracle), the sampling budget §2.5.

**BUILD (new, C/CUDA):** (i) the **trajectory kernel** (state-vector apply + Kraus-sampling + measurement-sampling
+ curand); (ii) the **host driver** (wave batching, codestate prep, schedule/Kraus marshalling, shot I/O); (iii)
the **correctness harness** (the §4 ladder: single-trajectory vs Python, distribution vs DM oracle, convergence).

---

## 6. Predictions / gates (predict-before-build)

- **P-A `(a)`:** MCWF ensemble mean = exact DM evolution (theorem); the sampler is unbiased. Routing: a
  *systematic* offset (beyond `O(1/√N)`) in the §4.2 check ⇒ a kernel bug; halt.
- **P-B `(b)`:** SV-MC↔DM TV `~ C/√N` (small code); pin `C` from the run. A miss (non-`1/√N` or a floor) ⇒ bias.
- **P-C `(b)`:** throughput ≫ the Python path; `10⁶ × R=10` in minutes. Pinned by the micro-bench before production.
- **P-D `(c)` gate:** `run_purpose="optimization"` selects complex64 only for the fused
  within-cycle SV-MC path and stamps `screening_only`; final/certification selects complex128 and
  stamps `c128_candidate`. A separate frozen c128 replay is required for any candidate conclusion.
- **P-E `(c)` gate:** RNG reproducibility — same base-seed ⇒ same shots (resumable); a positive control (different
  seed ⇒ different shots, same distribution within CI).

---

## 6.5 Pre-build gates — binding acceptance criteria (review 2026-06-20)

Five gates, registered before any coding; the build is not "done" until all pass. Gates 1–3 are pinned in this
doc; Gates 4–5 are enforced by Agent V + the reviewer before any production run.

- **Gate 1 — measurement INSTRUMENT spec (not just the POVM effect).** §1.5 pins the state update, decides whether
  `b` is a physical-POVM backaction or a classical reporting bias, and registers the ablation. Without this the
  `R>1` temporal-memory result is uninterpretable (a naïve `M_b=√E_b` Lüders update folds the readout classifier
  `b` into quantum backaction and can manufacture/erase temporal memory). **Grounded against the leakage /
  soft-readout literature before the instrument is frozen.**
- **Gate 2 — P4a/P4b scope split.** This build is **P4a-local** (9 data qutrits, no persistent ancilla);
  transport / CZ-hopping / ancilla-backaction is **P4b**. Stated in the header + §0; every claim scoped to
  local-leakage headroom.
- **Gate 3 — physically-sampled logical label.** The emitted label is `logical_flip = (sampled final physical
  readout) XOR (initial m)` — through the same registered readout model — **NOT** the input `m` and **NOT** an
  expectation-value threshold (§1). The teacher may know ground truth; the LEARNER's label must pass through the
  physical final readout (else the old "truth-to-invert" / perfect-artifact failure mode returns).
- **Gate 4 — small-scale DM-oracle convergence.** On a toy (3–5 qutrit / the 5-site sub-register, R=1–2) where the
  DM engine is exact, `TV(SV-MC, exact-DM) ~ C/√N` across `N∈{1e3,1e4,1e5}` (decreasing, within the sampling CI).
  Load-bearing certification (§4.2); the DM oracle must implement the **same registered instrument** (§1.5).
- **Gate 5 — throughput micro-bench before a large screening run.** Measure shots/s + peak memory
  for `R∈{3,5,10}`, complex64 vs complex128 before any `10⁶` optimization run. The benchmark
  may choose batching/wave geometry but cannot promote c64 into final/certification evidence.

---

## 7. Build plan (M3-scale: ≥3 disjoint agents + a separate reviewer)

- **Agent K (kernel):** `forward/kernels/sv_traj_d3.cu` (+ loader) — the trajectory MCWF kernel (state-vector
  apply, Kraus-sampling, measurement-sampling, curand, block reduction). Owns the `.cu`/loader.
- **Agent H (host):** `src/qec_twin/forward/scalable/sv_sampler.py` — the host driver (parse/Kraus marshalling,
  wave batching, codestate prep, shot I/O), the kernel interface.
- **Agent V (verify):** the §4 correctness harness under `outputs/` — single-trajectory vs Python, distribution
  vs DM oracle + `O(1/√N)`, throughput micro-bench, the complex64/128 + RNG gates.
- **Reviewer (un-led):** vet the kernel physics, the oracle ladder, no-toys/no-overclaim, before any production run.
- **Sequencing:** this design approved → interface contract (the kernel↔host data layout, the schedule/Kraus
  format) → the 3 agents build → reviewer → the §4 certification → the P4 `%ΔLER` runs.
- **Commit-gate:** all `src/qec_twin/**` (kernel, loader, host) HELD for user confirmation. Per the
  scripted-execution rule, every check/run is a committed script with asserts + printed evidence + a spawn guard.

---

## 8. Metric + rigor audit (house close)

**Metrics:** per-round LER + `%ΔLER` (reduction, positive=better; rung-1), TV (rung-1), the sampling-CI / power
(rung-1, the §2.5 budget). No new ledger rows — the SV-MC changes the *carrier*, not the *metrics*.

**Rigor:** `(a)` = the MCWF-exactness theorem, the byte-counts, the single-trajectory + apply-equivalence
identities. `(b)` = the `O(1/√N)` convergence constant, the throughput, the SV-MC↔DM TV band. `(c)` = the
precision/RNG/batching design choices + the GO/NO-GO from §2.5/P5. **No `(b)`/`(c)` used as a premise.** "Exact"
is reserved for the MCWF mean (a theorem) and operator identities — the full-d3 R>1 sampler is an unbiased
*estimate*, certified by the ladder, never called exact at full scale.
