# HANDOFF — notion-2 / notion-3 arc (2026-07-05)

For a new session taking over. Read this + `notion3_session_findings_2026-07-05.md` FIRST. The goal of this doc
is to let you continue WITHOUT re-walking the errors we already caught. Run the **`theory-fix` skill** on any
clean/surprising result before you build on it.

## 0. What the project is (do not drift)

Building the **error-coupling SIMULATOR** — a faithful forward generator of QEC syndrome records. Validity =
**faithfulness of the record vs INDEPENDENT oracles + anti-toy discriminability from a matched null**, measured
with the RIGHT observable. **NOT a digital twin** (no recovery / NLL-learner / do() / active probe-ladder — that
is a separate later project; [[feedback-simulator-is-goal-twin-is-next]]). **DEM/decoder/LER are OUT of the
validity chain** ([[feedback-simulator-not-decoder]]); K/CMI/p_ij are internal instruments. Classical 1/f =
scaffolding; **quantum GKSL bath = FINAL target** ([[project-coupling-nonmarkovian-is-the-contribution]]).

## 1. Current state (one paragraph)

**notion-2 (classical multi-time record memory) = PASS, broadly achievable** (record carries 1/f multi-time
memory distinguishable from a genuinely-Markov null, realistic coupling, controls fire). **notion-3 (quantum
non-classicality; K = Milz Kolmogorov violation = Budini DNI-violation) has been characterized ONLY through a
4-fold SUPPRESSING LENS** — `|++>` state (σx₁ ⇒ K sign-blind, CERTIFIED), X-only axis (misses the complementary
stabilizer), **pure σz-dephasing bath (crow_joynt: CLASSICALLY SIMULABLE by theorem ⇒ K limited by
construction)**, and coarse joint-parity K (twirls the common mode → DFS collapse at |r|=1). **DO NOT conclude
"notion-3 is fragile"** — that verdict is lens-conditioned, not established as intrinsic.

## 2. THE IMMEDIATE NEXT STEP (grounded, prereg ready, build NOT launched)

**`docs/twin_validation/notion3_relaxation_dualaxis_prereg.md`** — the fair notion-3 test:
- **Multi-component shared bath: σz dephasing (Tφ, classically-simulable) + σ− relaxation (T1, genuinely
  quantum, non-unital) — the σ− via a Lindblad collapse (no 2nd Fock mode, keep dim = 16·nmax).**
- **Dual-axis (X+Z): extract X_{d0}X_{d1} via ancilla a_X AND Z_{d0}Z_{d1} via a_Z; K on the JOINT (X,Z) syndrome.**
- **Independent-GT (strong, anti-toy):** build the crow_joynt explicit classical field that reproduces the
  dephasing sector → verify K→0 CONSTRUCTIVELY (not by fiat); show the relaxation-sector K EXCEEDS it.
- **Prediction:** relaxation K is ROBUST (broad, not corner/sign-blind/DFS) ⇒ notion-3 was lens-suppressed.
  **Falsifier:** relaxation K also fragile on dual-axis ⇒ notion-3 IS intrinsically fragile. Both real findings.
- **Build org:** reuse `notion3_ancilla_mediated_run.py` v2 verbatim (build_L2, joint-parity, K_stat, controls);
  add σ−, the Z-ancilla, joint-K, the crow_joynt null. Scouts + builder + smoke + un-led reviewer, then serial run.

## 3. ERRORS ALREADY CAUGHT — do NOT repeat (each maps to a `theory-fix` trip-wire)

1. **Do NOT run r<0 / a differential-vs-common sweep on the |++> carrier expecting a K asymmetry.** CERTIFIED:
   σx₁ L(r)σx₁ = L(−r) ⇒ **K(r)=K(−r) EXACTLY** (`notion3_sign_symmetry_control.py`, sha f4610a33). r=+1 and
   r=−1 are σx₁ MIRRORS; K = f(|r|), sign-blind. The rate papers (wang/hatifi/szankowski) govern the dephasing
   RATE, NOT K. To test a genuine SIGN effect you MUST break σx₁ (Bell/computational init). [[project-jointparity-K-sign-blind-sx1]]
2. **Do NOT use `X − matched-marginal-null` as a discriminator (error A).** Measure the ABSOLUTE multi-time
   order statistic (CMI / G² / Kolmogorov). [[feedback-simulator-is-goal-twin-is-next]]
3. **Do NOT claim the classical memory is "first-order" (error C).** It is 2nd-order (covariance) / 4th-order
   (CMI); κ-scaling slope ≈ 3.7. Grounded (Quiroz/Srivastava/Dong).
4. **Do NOT couple the bath to ONE data qubit and call a joint-parity measurement a "stronger twirl".** With d1
   inert, X_{d0}X_{d1} ≡ X_{d0} (a tautology). Always assert record(test) ≠ record(null) > tol.
5. **Do NOT trust `[ours]` reading-note quantitative extrapolations as citations.** The `K∝(1∓|r|)²` `[ours]`
   inference was rate-not-K and got falsified. Verify against the actual object.
6. **Do NOT reach for OQuPy on the single-pseudomode target** (24 GB / 43 min for one long-memory mode); use
   numpy/QuTiP exact-Fock. OQuPy is validated infra for the CONTINUUM/1-f future. [[reference-bath-simulation-pipelines]]
7. **Do NOT present C_pf and M_mem as independent memory axes** — on the symmetric records they degenerate
   (C_pf ≡ M_mem). 

## 4. Committed artifacts (all in `outputs/twin_validation/`, gitignored local; sha in each prereg §8/§10)

- `corrected_multitime_observable_run.py` (notion-2 PASS, sha 2560478e)
- `notion3_quantum_vs_classical_run.py` (notion-3 separation, sha 7bef2895)
- `notion3_ancilla_mediated_run.py` (v2 faithful carrier, sha 823342df)
- `notion3_Kpeak_diagnostic_run.py` (peak real+converged, sha a55982df)
- `notion3_sign_symmetry_control.py` (CERTIFIED sign-blind, sha f4610a33)
- `notion3_oqupy_pipeline.py` + `notion3_qutip_pipeline_compare.py` (independent-GT + tooling)
- `quantum_backaction_{c4analog,deepen,fairtest}.py` (the both-bases + pseudomode-K anchors)

Preregs (in `docs/twin_validation/`): `corrected_multitime_observable_prereg.md`,
`notion3_quantum_vs_classical_prereg.md`, `notion3_ancilla_mediated_prereg.md` (§8-10 = v1-tautology finding +
v2 result), `notion3_coupling_geometry_prereg.md` (⚠ header: sweep is a mirror tautology — DO NOT run),
`notion3_Kpeak_diagnostic_prereg.md`, **`notion3_relaxation_dualaxis_prereg.md` (the next step)**.

Memory: [[project-cpdiv-notion-hierarchy-passive-record]] (notion-2/3 results), [[project-notion3-dfs-coupling-geometry]]
(DFS grounding + sign-blind correction + crow_joynt reframe), [[project-jointparity-K-sign-blind-sx1]] (certified),
[[reference-bath-simulation-pipelines]], [[feedback-theory-fix-trip-wires]].

## 5. How to run (environment)

- Repo on WSL: `\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC`. Python:
  `/home/cx/miniconda3/envs/aiqec/bin/python` (conda not on the non-interactive PATH).
- Run via wsl.exe, capture the exit INSIDE wsl to defeat the quote-chain trap: `... ; echo "python-exit=$?" >> log`.
- CPU exact-DM (small); **no GPU concurrency; workstation is the user's live desktop.** Scripted-execution:
  committed script, asserts, printed evidence, flush, `__main__` guard, GATE_RESULT, sha256 sidecar.
- Ultracode ON: use Workflow for substantive builds (scouts → builder + smoke → un-led reviewer, then serial run).

## 6. Literature (full ledger in the findings note §3)

Key: **crow_joynt 1309.6383** (dephasing classically simulable, relaxation NOT — THE reframe) · **budini
2301.02500/2411.13471** (K≡DNI, superclassical) · **wang/hatifi/layden/botzung** (DFS — govern the RATE) ·
**Milz 1907.05807 / Kam 2410.23779** (the observable) · **chain_mapping 2407.10140** (multi-component bath model)
· **shen/QMCtwin 2606.19848** (positioning: our gap = K on multi-round records vs coupling geometry).
