# Session handoff — soft-readout (③) phase

**How to use:** start a new session, then paste *"继续 qec_twin —— 先读
`docs/nonpauli_teacher/SESSION_HANDOFF_soft.md` 完整继承上个会话的状态/纪律/操作模式,简述理解后从 soft D1 接续"*,
or paste this file's content directly. The persistent **memory** (`MEMORY.md` + the memory files) auto-loads and
carries the durable lessons; this file adds the live state + operating model + the most lethal disciplines.
(Written in English per the docs-in-English rule; the project is bilingual — reply in the user's language.)

Repo: `\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC`, branch `Dev-F`, conda env `aiqec`, GPU RTX 5090 / WSL2.

## Mission / end goal
Non-Pauli leakage **teacher–learner** (sim-only): **teacher** (controlled XZZX-surface circuit injecting
leakage / T1·T2 / coherence → emits faithful `(soft-syndrome, logical)` data) → **learner (A)** (recovers a
richer-than-Pauli noise model) → decoder → scored by **%ΔLER vs the Pauli-DEM floor + gap-to-Bayes-floor**.
The Pauli **DEM is the baseline/foil** (proven insufficient — leakage is NOT DEM-reducible). End goal: the
teacher PRODUCES faithful surface code, d3 → d5/d7 (ADR 0007, C = R3).

## Where we are
1. **Carrier (the scalable teacher) is BUILT + honestly CERTIFIED.** Engine = **quimb** (torch backend, c128).
   Two carriers: **MCWF-MPS forward** (`src/qec_twin/forward/scalable/mps_forward.py`) + **LPDO floor**
   (`src/qec_twin/audit/floor_backend_tn.py`, `TNPathEvaluator`). **DM = oracle**
   (`src/qec_twin/forward/exact/qutrit_dm.py`). Backend-agnostic via **`PathJointEvaluator`**
   (`src/qec_twin/audit/floor_backend.py`, DM backend `DMPathEvaluator`). Estimable floor = **exact-per-sample
   MC** (model-based, unbiased) in `src/qec_twin/audit/bayes_floor.py`. Seam + matched-Pauli-DEM foil in
   `src/qec_twin/forward/scalable/seam.py`. **Full-d3 carrier-vs-DM bit-exact 7.28e-12**; honest cert =
   `outputs/teacher_prereg/p7h_carrier_cert_HONEST.md`. Caveats: χ*=4 is τ=1e-3-grade (NOT bit-exact); LPDO
   arm-C unimplemented; **d7 PROVISIONAL** (no oracle). All carrier `src/` is **STAGED, not committed**.
2. **⑦ (first science result) DONE** — `docs/nonpauli_teacher/p7_leakage_ler_effect.md`: **leakage DOES raise
   the optimal LER** (ΔF = F_leak − F_bg > 0, 8/8 cells exact, z up to +7.69, monotone in rate+R); **but BINARY
   readout has NO decodable non-Pauli headroom over the best (moment-matched) Pauli** (capped, headroom_recal
   small, |z|<2) → confirms the pivot to **soft readout**. Caveat: sub-register precision; recal foil == blind
   foil on the small graphs.
3. **CURRENT TASK: soft readout (③)** — soft is the lever that unlocks the leakage headroom (the |2⟩/coherence
   is visible in the IQ analog readout that hard-thresholding discards). D1 grounding was started+interrupted;
   grounding numbers already in hand: **soft LER reduction ~6.8%** (AlphaQubit / Bausch et al. + Ali et al. d3
   bit-flip — two independent convergent numbers); **Pattison +25%-over-optimal-hard-threshold ceiling**;
   **whether the Google datasets ship IQ/analog data is UNRESOLVED → check `docs/.datasets/`** (data-grounded =
   strongest; else literature-grounded + a declared bracket).

## Operating model (user directive — follow it)
**Self-driven loop, every block passes review before the next:**
`build a block → 3-lane un-led 省察 (L-grounding/faithfulness · L-method/numerics · L-red-team/epistemic; each
lane gets ONLY the stage problem + the artifact, NOT your conclusions/expected answers) → META-省察 (the
orchestrator audits the review itself: per lane — did it test the informative thing, can its check fail,
independent reference, is the verdict earned, what did it not cover; cross-check lanes + adjudicate
disagreements; gap-hunt) → proceed only if it withstands, else send the weak lane back / add a lane / launch an
independent from-scratch adjudication`.
**Soft deliverable sequence:** D1 grounding + pre-reg (the IQ model: per-state |0⟩/|1⟩/|2⟩ IQ blob + likelihood
+ the |2⟩ leakage signature) → D2 soft emission (extend the forward to emit IQ data) → D3 soft Bayes floor (the
optimal LER under the soft likelihood) → D4 soft foils + headroom (soft-aware decoder vs hard-threshold→Pauli-DEM;
**headroom = does soft unlock the leakage contribution binary couldn't**).
**慢就是快 (slow is fast); unlimited token budget; ALL commits STAGED, not committed (user confirms on return);
GPU-heavy agents serialize (exit-9 oversubscription lesson), reviews run GPU-light in parallel; docs in English.**

## Disciplines (blood-bought; full text in memory — the most lethal re-stated)
- **Grounding above all — the #1 soft toy-risk is INVENTING an IQ model.** Every physical parameter (SNR / blob
  separation / |2⟩ position) must be data > literature > a declared bracket — **never a pinned arbitrary
  constant** (a too-separated |2⟩ blob hands the answer / fakes the headroom).
- **Anti-toy / FAITHFULNESS** (`docs/FAITHFULNESS_PROTOCOL.md`): (I) verify vs INDEPENDENT ground truth (raw
  artifact / closed form / from-scratch — NEVER engine-vs-itself; circular verification is the root of every
  toy); (II) a constraint ledger + a falsifying test for each (must be able to FAIL); (III) declare + BOUND
  every simplification, unbounded = STOP.
- **No rubber-stamp** (`feedback-scrutinize-vacuous-checks`): never relay an agent's PASS at face value. Vacuous
  patterns: renorm-masked, R=1-trivial (for an R-accumulating effect), internal-circular (carrier-χ vs
  carrier-exact ≠ vs the independent oracle), structural-can't-fail (ρ=XX† positive by construction). Ask: could
  it fail? informative regime? independent reference? summary == body? engine-vs-itself (c128-vs-c64) ≠
  correctness. **no-d3-guarantees-d7.** **And the REVIEW's results are themselves audited (meta-省察).**
- **Physical-pulse vs frame** (`feedback-clifford-invariant`): real d3 has per-round transversal X/Y DD echoes —
  detector-invariant but DECISIVE for leakage (dropping them over-states |2⟩ up to 504×); the post-M Y echo
  deterministically flips the logical at R≥2 — the decoder needs the `CY rec[..]` frame correction (the src seam
  may still need this — a follow-up).
- Heavy task ≥3 disjoint agents + an un-led reviewer; don't-lead-the-reviewer; scripted-execution (committed
  scripts + asserts + printed evidence + flushed + `__main__` guard); `external/` baselines pristine.
- **The user is a rigorous skeptic — this session they caught 3 cert over-reports + several toys. The new
  session must out-skeptic the user: distrust every "too-good" result (its own AND every agent's) earlier than
  they would.**

## Key pointers
- docs: `ADR 0010` (carrier decision), `p7b_estimable_floor.md` (the floor), `p7_leakage_ler_effect.md` (⑦),
  `p7h_carrier_cert_HONEST.md` (honest cert), `FAITHFULNESS_PROTOCOL.md`, `CLAUDE.md`, `docs/.datasets/`
  (Google data + the IQ-data question).
- perf TODO: the LPDO floor is ~1000×/path slow (Python B-loop) → needs **batched-B / CUDA-C++** before
  soft/production scale (the user's suggestion).
- All `src/` changes are staged-not-committed; commit awaits the user.
