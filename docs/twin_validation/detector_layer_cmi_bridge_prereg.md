# Pre-registration — (B) detector-layer bridge: does the source non-Markovianity survive the detector map?

**Date 2026-07-01. Theory-first (Kam-anchored), pre-code.** The record-layer §3b-followup established that a
single measured qubit + persistent pseudomode produces a measurement RECORD `M_t` beyond finite-order
classical Markov (beyond-Markov-2 at λ≤0.30). **This experiment asks the DECODE-RELEVANT question:** when
`M_t` is a stabilizer syndrome and we form the DETECTOR stream `D_t = M_{t-1} ⊕ M_t` (the object a decoder
actually consumes), does the beyond-Markov temporal structure SURVIVE the differencing map, or COLLAPSE to
low order? Classes: **(a) exact**, **(b) prediction band**, **(c) gate**.

## 0. What is grounded (checked; no reinvention)
- **The detector construction + the siting law are Kam's** (`docs/papers/reading_notes/
  kam_nonmarkovian_surface_code_2410.23779.md`, 精读): `D_{s,t} = M_{s,t-1} ⊕ M_{s,t}` (Eq 2); error CLASSES —
  Class-0 DATA, Class-1 SYNDROME/SPAM, Class-2 gates; **DATA-qubit temporal correlations are BENIGN, but
  SYNDROME/ancilla-qubit correlations are CATASTROPHIC (timelike strings)**; and **the 2-point detector
  autocorrelation is INSUFFICIENT** — use a multi-time statistic. ⇒ the observable (detector-layer multi-time
  CMI), the SITING contrast (data vs ancilla), and the metric (CMI ladder, not 2-point) are all Kam-grounded.
- **The estimator (CMI/G² Markov-order ladder) is the two-panel-validated one** from the §3b-followup
  (`outputs/pilotB_markov_order_owned_vs_unowned.py`; independent re-implementation match 2e-10, χ² calibration
  FPR≈0.05, seed-robust). Reuse verbatim on both `M_t` and `D_t`.
- **The error mechanism is the CERTIFIED pseudomode dephasing block.** `H = w·b†b + g·σ_x^{(q)}(b+b†)`, Lindblad
  `√(2λ)·b` is the independent-boson / Garraway pseudomode PURE-DEPHASING model in the x-basis (the coupled-
  pseudomode pilot certified it vs the closed-form dephasing function to 2.5e-8). σ_x-dephasing is TWO-WAY
  (drives repeated bit-flip-type errors a Z-stabilizer detects), unlike one-shot relaxation. SAME coupling type
  for both sitings ⇒ an apples-to-apples Kam contrast.

## 1. Mechanism / circuit (ANCHORED, minimal faithful = single stabilizer)
State on **2 data (d0,d1) ⊗ 1 ancilla (a) ⊗ 1 pseudomode (nmax=8)** = **64-dim** (exact DM, safe). Z-repetition
(bit-flip) code, one stabilizer `Z_{d0}Z_{d1}`. Per round `t`:
1. **Idle-evolve** DT under the arm's GKSL `dρ/dt = -i[w b†b + g σ_x^{(q)} (b+b†), ρ] + D[√(2λ) b]`, `q` = the
   coupled qubit (mode NOT measured — carries the memory).
2. **Syndrome extract:** `CX(d0→a)`, `CX(d1→a)` (ideal), ancilla started `|0>`.
3. **Born-measure a in Z → `M_t`**; collapse `ρ → P_{a=m} ρ P_{a=m}/Tr` (project ancilla only; data+mode untouched).
4. **Reset a → |0>**; repeat. `R=8` rounds; `D_t = M_{t-1} ⊕ M_t`.
- **Two ARMS (the Kam contrast, same coupling):** `q = d0` (**DATA**, Class-0) vs `q = a` (**ANCILLA**, Class-1
  measurement error). Data init `|00>`, ancilla `|0>`, mode vacuum. Regime **λ=0.15** (the seed-robust record-layer peak).

## 2. Observable (the RIGHT one — Kam-grounded, multi-time, DUAL-LAYER)
The validated **CMI/G² order ladder** (`I(x_t;x_{t-2}|x_{t-1})` order-1, `I(x_t;x_{t-3}|x_{t-1,t-2})` order-2)
computed on **BOTH** the raw syndrome `M_t` AND the detector `D_t`. The decode-relevance signal is the CONTRAST
`order(D_t)` vs `order(M_t)`. (2-point autocorrelation carried only as a Kam-insufficient reference.)

## 3. Predicted behavior (falsifiable) + epistemic classes
- **(a) EXACT:** `D_t = M_{t-1}⊕M_t` is a deterministic, information-LOSSLESS transform of the record given
  `M_0` (`M_t` reconstructable from `D_{1..t}, M_0`); differencing is a HIGH-PASS filter (a constant/slow syndrome
  offset cancels). A Markovian source (wide λ / mode reset) ⇒ round-independent detectors (order-0/1).
- **(b) BAND — falsifiable, BOTH outcomes weighty, NOT pre-committed:** does `order(D_t)` COLLAPSE (drop below
  `order(M_t)`, truncate at k≤2) or SURVIVE (≈ `order(M_t)`)?
  - **Collapse** ⇒ the source non-Markovianity is decode-BENIGN — a k≤2 temporal decoder edge captures it; the
    simulator is irreplaceable for STATE fidelity but not for the decoder. **Predicted MORE likely for the DATA
    arm** (Kam Class-0 benign).
  - **Survive** ⇒ genuinely long-range DETECTOR correlations that marginalized/Markov decoders miss; simulator +
    non-Markovian decoder both needed. **Predicted MORE likely for the ANCILLA arm** (Kam Class-1 timelike strings).
  - **CAVEAT (why NOT foregone):** the high-pass intuition assumes LOW-FREQUENCY (drift) memory. At λ=0.15 we are
    deep UNDERDAMPED (g/λ=2.8, vacuum-Rabi REVIVALS) ⇒ memory is OSCILLATORY, which differencing need NOT remove
    (can alias). So collapse is a genuine bet, not a theorem.
- **(c) GATE:** `p<0.05` order rejection; `CMI>2×floor`; seed-stable (≥3 seeds); NMAX-converged (6 vs 8).

## 4. Independent ground-truth (Rule I, non-circular)
- **Propagator:** cross-check the batched-expm one-round evolution vs qutip `mesolve` (independent integrator),
  dim≤16 slice, to ≤1e-6; and the single-qubit σ_x-dephasing coherence vs the independent-boson closed form
  (the pilot's certified oracle). Records are then exact-DM sampled (no trajectory approximation) at 64-dim.
- **Estimator:** the reused ladder ships its TRUE-Markov-1/2/3 calibration+power asserts (must pass before any
  verdict). **Controls:** (i) **Markovian arm** (wide λ) ⇒ `D_t` MUST be low-order (positive control the collapse
  is real, not a differencing artifact); (ii) **g=0** ⇒ `M_t` degenerate (sanity); (iii) **seed-robustness** ≥3
  independent physics seeds (a same-seed re-run is only a determinism check — [[feedback-adversarial-self-verification]]).

## 5. Bounded simplifications (Rule III)
- **(c) single stabilizer (2 data+1 ancilla), not full d=3** — the TEMPORAL differencing question is fully
  exercised on one stabilizer's time series; spatial d=3 error-correction is Stage-2 (MCWF, certified vs this
  exact-DM). **HARD: full d=3 + mode dense-DM Liouvillian ≈ 22–68 GB ⇒ OOM-forbidden** (workstation crash regime);
  Stage-2 MUST use state-vector MCWF, never dense DM.
- **(c) Fock truncation nmax=8** — bounded (§3b-followup: nmax=6 converged for λ=0.15); re-checked here.
- **(c) ideal CNOTs / ancilla reset** — the error is sited by the arm (data vs ancilla); gate/reset errors are a
  separate (deferred) Class-2 axis.

## 6. Build plan (outputs/ first; committed script)
`outputs/pilotB_detector_layer_cmi.py`: 64-dim exact-DM batched-over-shots; both arms + Markovian control at
λ=0.15; per arm compute the CMI ladder on `M_t` and `D_t`; propagator certified vs mesolve; estimator
calibration asserts; seed-robustness ≥3; nmax 6-vs-8 check. Print the `order(M)` vs `order(D)` contrast per arm
and the DATA-vs-ANCILLA contrast. Dim guard (≤64). Reviewer before any decode-relevance claim.

## 7. Verdict (provisional, pre-code)
GROUNDED: detector construction + siting law + insufficiency-of-2-point (Kam), the validated estimator, and the
certified pseudomode dephasing block all exist; the dual-layer CMI contrast and the two-siting design are the
Kam-faithful way to ask whether the source non-Markovianity is decode-relevant. The load-bearing OPEN question —
collapse vs survive, per siting — is what the run decides. PROVISIONAL until measured; either outcome is a real,
reportable finding.

## 8. Post-run results + the differencing/collider artifact (2026-07-01, post-run amendments)

**(1) Raw-CMI(D) readings were INVALID — the differencing/collider artifact.** `D=M⊕M` is a deterministic
function of a Markov chain (Burke–Rosenblatt 1958 ⇒ generically not finite-order Markov); conditional
statistics on D suffer collider bias (D_{t+1} is a collider; conditioning opens D↔D paths). Pre-registered
check (`outputs/pilotB_differencing_artifact_check.py`): for **i.i.d.** M, CMI2(D)=1.28e-2 @p(M)=0.050,
2.19e-2 @0.085, peak 2.69e-2 @≈0.145 (non-monotone — the monotone bet missed), ≈floor @p≈0.5. Consequences:
the ANC-Markov "control failure" was ≈93% pure artifact (not measurement-mediated mode memory — that story is
retracted); the ANC arm's absolute CMI2 (2.11e-2) sits INSIDE its matched-marginal null (2.19e-2); the
ANC-vs-DATA contrast was an M-marginal confound (0.085 vs 0.477). Duality: pairwise D-correlation @lag≥2 is
exactly 0 for memoryless M (artifact-clean, Kam-insufficient); conditional multi-time stats are powerful but
collider-confounded ⇒ **matched-marginal Markov-k surrogate nulls are MANDATORY for any conditional
detector-stream analysis, incl. real hardware** (novelty pending literature check; pij/DEM-based practice is
largely immune since it models the XOR structure).

**(2) The corrected instrument + results (`outputs/pilotB_detector_surrogate_null.py`, K=200/fit, M records
saved).** Fit Markov-1/2 to observed M → surrogate ensembles → XOR → null distributions of CMI(D); excess =
observed − null, empirical p. **ANC arm: pre-registered honest-negative CONFIRMED** (CMI1 excess +1.3e-3
p=0.14; CMI2 excess −1.2e-3 p=0.94; observed slightly BELOW the M1-fit null, a mild opposite-direction
lack-of-fit, noted only). **DATA arm: the no-excess bet is FALSIFIED at the CMI1 rung — a REAL detector-layer
excess: +4.68e-4 = 34× the null, p_emp=0.000 (0/200), magnitude ≈ M's own CMI2 (4.90e-4)** — the source's
beyond-Markov-2 syndrome structure passes ~losslessly into the detector's conditional statistics in the
phantom-free regime (M-marginal≈0.48). This INVERTS §3's naive binary reading: the ANC "survive" was phantom;
the DATA "collapse" hid the genuine signal. Hardware-relevant: real raw syndromes accumulate to marginal≈0.5
(the DATA-arm regime) ⇒ phantom small there, but real M is non-i.i.d. so the surrogate null remains mandatory.
**STATUS: PROMOTED (2026-07-01, `outputs/pilotB_data_excess_promotion.py`).** The gate passed 4/4: three
independent physics seeds each show the CMI1(D) excess over their own K=100 M2-fit surrogate null at
p_emp=0.000 (excess +4.69e-4 / +4.56e-4 / +2.31e-4 — verdict seed-robust, magnitude carries ~±50% seed
scatter), and the nmax 4→6 truncation check shifts the excess by only 2% (<30% gate). **Promoted claim
(scoped): at code-realistic error rate, the DATA-sited non-Markovian source's beyond-Markov syndrome
structure genuinely reaches the decoder-facing detector layer — a conditional (CMI1-rung) excess over the
matched-marginal Markov-2 surrogate null, ≈ M's own CMI2 (near-lossless transfer) in the phantom-free
regime (M-marginal≈0.48).** Still scoped: single-stabilizer instance, one (g,λ,dt) point, excess at the
CMI1 rung of D; reaching the detector layer is the NECESSARY condition for decode-relevance — the ΔLER
question remains the deferred decoder layer.
