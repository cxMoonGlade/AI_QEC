# Axis-A Teacher — Pre-Registration (theory-first, before any run)

Status: PRE-REGISTRATION. 2026-06-24. Supersedes the earlier `axisA_correlated_pauli_teacher_prereg.md`
(which regressed to a Pauli-only teacher = a toy). Theory-first: the predictions are written BEFORE
the run.

## 0. What the Axis-A teacher must be — Pauli + non-Pauli, the full realistic mix

The Axis-A teacher is the CONTROLLED known-truth teacher for the validated causal noise twin. It must
be a **faithful, realistic d3 XZZX noise model carrying BOTH Pauli AND non-Pauli mechanisms together**,
because:

- A real device has stochastic Pauli + coherent + T1/T2 (non-unital) + leakage + correlations **all at
  once**. A SINGLE-mechanism teacher (Pauli-only, OR leakage-only, OR coherence-only) is itself a TOY —
  it is neither faithful nor a fair test of the twin.
- The iid-Pauli LEARNER (the twin's baseline model class) FITS the Pauli part (well-specified there) but
  GENUINELY MISSES the non-Pauli + correlated parts. **The misspecification the twin must handle = the
  non-Pauli + correlated EXCESS over the iid-Pauli baseline.** Pauli lives on BOTH sides — the teacher's
  realistic baseline AND the learner's model class; the gap between them is the validation target.

So: NOT "Pauli teacher" (no gap → nothing to validate → the earlier toy); NOT "leakage-only teacher"
(unfaithful + under-tests); but the FULL mix, with the gap = the non-Pauli/correlated excess.

## 1. The teacher's mechanisms (it carries all; the learner is iid-Pauli)

| Mechanism | class | iid-Pauli learner | observable in the record via |
|---|---|---|---|
| Stochastic Pauli baseline (SI1000-like depol/gate/idle) | Pauli | **FITS** (well-spec) | detector marginals |
| Coherent over-rotation (rx/rz miscalibration) | non-Pauli, unitary | **misses** | EXCESS LER (PTA-underestimate; terminal/data; theory-backed, largest at d3) |
| Non-unital T1 / amplitude-damping | non-Pauli, non-unital | **misses** | round-to-round detector CORRELATION (the built-teacher finding ~2.6e-3; iid-Pauli structurally cannot fit) |
| Leakage (qutrit \|2⟩) | non-Pauli, leakage | **misses** | LEAKAGE SIGNATURE — cross-round correlated/persistent detector firing |
| Spatial / temporal correlations (crosstalk, drift) | non-iid | **misses** | detector COVARIANCE / cross-round correlation |

## 2. First-principles claim (theory-first)

- class (a) EXACT: the iid-Pauli learner is closed under the detector MARGINALS (it always fits the
  single-detector rates = the Pauli baseline). But the non-Pauli + correlated mechanisms each inject a
  signal in a HIGHER moment / different sector the iid-Pauli class cannot represent at the fitted
  marginals: coherence → excess LER (terminal sector); non-unitality → round-to-round correlation;
  leakage → the cross-round leakage signature; spatial/temporal correlation → detector covariance. Each
  residual = the misspecification, and each is a function of the STANDARD record (syndrome stream +
  terminal readout) — i.e. OBSERVABLE (the lesson from the coherence redirect: coherence alone is
  syndrome-blind, visible only via excess-LER; the non-unital/leakage/correlation parts ARE in the
  syndrome stream).
- class (b) PREDICTION BAND: per-mechanism magnitudes (e.g. non-unital round-corr ~2.6e-3 at γ=0.04;
  coherent excess-LER grows with θ,R; leakage signature with the leakage rate) — registered, a miss is
  a finding.
- class (c) gate: the per-mechanism z-detectability thresholds at the d3 shot budget.

## 3. Known-truth (exact) substrate

d3 qutrit density matrix (3^n, ~2 GB GPU) is EXACT → the full Pauli+non-Pauli teacher's joint (s,f)
record distribution is exactly computable → the twin is validated against EXACT truth. This is the
white-space anchor (known truth that real hardware cannot provide).

## 4. Existing build + the gap to close

`outputs/teacher_prereg/twin_xzzx_teacher.py` (real XZZX d3, 2026-06-23) already carries **coherent rx
+ non-unital amp-damp** (stim-cross-validated, within-cycle-faithful). The GAP to the full Axis-A
teacher: add (i) an explicit stochastic **Pauli baseline** (the part the learner fits), (ii) **leakage**
(qutrit \|2⟩ population, via the validated MCWF carrier), (iii) **spatial/temporal correlations**. All
remain exact-checkable against the d3 qutrit DM.

## 5. Next steps (gated)

1. extend the built teacher to the full Pauli + non-Pauli + correlated mix (above);
2. **0c hardened gate** — the syndrome-vs-terminal-data chain-rule split (so the gate self-certifies
   WHICH observation surface carries EACH mechanism's signal) + fix the Y-echo LER convention;
3. independent un-led review of THIS teacher design;
4. build the UQ layer (bands + conditional coverage; SBC/TARP/conformal) on the full teacher.

## 6. Why this is right (vs the two toys I passed through)

- Pauli-only teacher (my first regression) → learner fits it → NO misspecification → nothing to
  validate.
- leakage-only / single-non-Pauli teacher (my overcorrection) → unfaithful (real noise is the full mix)
  + under-tests the twin.
- the FULL Pauli + non-Pauli + correlated teacher → faithful AND the misspecification (the non-Pauli +
  correlated excess over the iid-Pauli baseline) is exactly what the twin's UQ/counterfactual must
  honestly handle. This is the realistic, compelling Axis-A.

## 7. Refined per-mechanism build contract (2026-06-24, confirmed; theory-first, before the run)

Confirmed scope (user, 2026-06-24):
- **STAGED build.** Batch 1 = the four SINGLE-SITE mechanisms (Pauli baseline + coherence[built] +
  non-unital[built] + leakage), taken through the 0c gate + an un-led review, BEFORE batch 2 adds the
  two-site SPATIAL correlation. (Temporal correlation is partly emergent from non-unitality/leakage +
  an explicit round-dependent drift schedule, single-site, so it rides batch 1; only the genuinely
  two-qutrit spatial crosstalk is deferred to batch 2.) The END teacher is the full mix; the build
  stages single-site → +spatial. Single-mechanism is still a toy — batch 1 already carries Pauli +
  three non-Pauli together.
- **Independent GT = a NEW multi-round exact record oracle on the d3 qutrit DM** (mainline `QutritDM`
  extension, commit-gated), bounded per §7.2.
- **Build org = 3 disjoint-ownership builders + an un-led reviewer.** Long production runs are driven by
  the orchestrator in self-controlled background, NOT inside a sub-agent (the 2026-06-23
  delegated-long-job-killed lesson, `project-twin-axisA-gate-result`).

### 7.1 Per-mechanism contract — observable surface (DERIVED first) × exact d3-DM GT × bounded simplification

| # | Mechanism | class | OBSERVABLE surface (derived, theory-first) | exact d3 qutrit-DM INDEPENDENT check (non-circular) | bounded simplification (declared; unbounded ⇒ STOP) |
|---|---|---|---|---|---|
| ① | Stochastic Pauli baseline (new) | Pauli | detector MARGINALS + flip rate; the iid-Pauli learner FITS these exactly (closed under marginals = class (a)) → the well-specified floor | stim reproduces the full (s,f) exactly (extend the bit-flip slice to a full `PAULI_CHANNEL`); DM marginals agree. stim is implementation-independent | siting (per-CZ vs per-round lumped — reuse S1 machinery); rate grounded to SI1000 (declare version+settings, baseline discipline) + SWEPT, never frozen |
| ② | Coherent over-rotation `rx(θ)` (built) | non-Pauli unitary | EXCESS LER (PTA-underestimate; terminal/data readout; theory-backed Bravyi/Marton-Ásbóth/Zhao-Liu, largest at d3) — NOT the syndrome stream (measurement-twirled, Beale et al.) | unitary exact on the DM; excess-LER = LER_teacher − LER_best-Pauli-foil under one FROZEN decoder; R=1 cross-checks the §3 analytic KL(R=1)=0 + R-growth | θ declared + SWEPT; the twirl→excess-LER magnitude at d3 is small (declared) |
| ③ | Non-unital T1 / amp-damp `γ` (built) | non-Pauli non-unital | round-to-round detector CORRELATION (~2.6e-3 @ γ=0.04; an iid-Pauli foil factorizes ⇒ structurally cannot fit) + a |0|/|1|-asymmetric R=1 marginal | amp-damp Kraus exact on the DM (1-qutrit cross-check built); the round-to-round correlation computed EXACTLY on the DM (R=2 marginal-pair) vs carrier MC | per-CZ vs lumped (S1=0.96 declared); γ SWEPT |
| ④ | Leakage \|2⟩ (new) | non-Pauli leakage | cross-round leakage SIGNATURE: \|2⟩ persists across rounds (inert under qubit gates) ⇒ persistent/correlated detector firing + the swept-b leaked readout (`F1=\|1⟩⟨1\|+b\|2⟩⟨2\|`); a LONGER-lag memory than amp-damp | use `forward/channels.py:leakage_kraus` (Wood–Gambetta); CPTP + C_L>0 vs the INDEPENDENT qutip reference (`wg_leakage_channel_reference.py`); \|2⟩-population trajectory exact on the DM; b SWEPT (σ₂ prevent-toy lesson) | WG (ω, g_seep) grounded to literature + SWEPT; leaked-readout b bracketed + SWEPT; per-CZ injected rate vs duration-integrated (T4 trap — declared; d3 uses per-CZ) |
| ⑤ | Spatial / temporal correlation (BATCH 2 for spatial) | non-iid | SPATIAL: detector COVARIANCE cov(det_i, det_j) same round, different stabs (iid factorizes ⇒ cannot fit). TEMPORAL: drift = round-dependent (θ_r, γ_r) + long-lag correlation | a two-site Kraus applies EXACTLY on the dense DM; spatial covariance computed exactly at R=1 vs carrier | crosstalk model (NN-ZZ vs correlated-depol) declared; strength SWEPT; the two-site apply is a NEW capability (batch 2) |

The full-mix misspecification = (② + ③ + ④ + ⑤) EXCESS over the ① iid-Pauli fitted floor. Pauli lives on
BOTH sides (teacher floor + learner class).

### 7.2 Independent ground-truth feasibility bound (declared; prevent-toy honesty)

The full-9-qutrit DM is `3^9² × 16 B ≈ 6.2 GB / copy`; the exact record enumeration recurses to depth
`n_stab·R` with a state copy per branch level. Therefore the exact DM oracle is bounded:
- **R=1:** the FULL exact (s,f) joint (256 syndromes × 2 logical) is feasible — the gold-standard
  independent GT.
- **R≥2:** the full `2^(8R)` joint is memory-infeasible (R=2 ≈ 100 GB) ⇒ the exact DM GT at R≥2 is the
  exact per-detector MARGINALS + round-to-round + spatial detector CORRELATIONS (the very moments an
  iid-Pauli foil cannot match), via the marginal projectors — NOT the full joint.
- The MCWF carrier (`3^9` state vector ≈ 0.3 MB) is the scalable sampler, certified against the DM on
  exactly these exact quantities (Gate-4 style) + the Clifford slices vs stim + the WG channel vs qutip.

⇒ §3's "the full joint is exactly computable" is REFINED to: R=1 full joint exact; R≥2 exact
marginals/correlations. This is the bounded, honest GT, not an unbounded "full exact at all R".

### 7.3 0c hardened gate (runs after the batch-1 mechanisms land)

1. **LER convention fix:** `logical_error(obs, R) = obs XOR ((R-1)·|logical_supp|) mod 2` (derived +
   oracle-checked; already asserted in `noiseless_smoke`). Every decoder-scored metric uses it ⇒ unblocks
   the coherent excess-LER (②).
2. **syndrome-vs-data chain-rule split:** `KL_full = KL(syndrome-stream) + E_s[ KL(terminal-data | s) ]`,
   measured PER-MECHANISM (ablation on/off), so the gate self-certifies which observation surface carries
   each mechanism's signal (② → terminal-data; ③/④ → syndrome stream) and would correctly NO-GO a
   syndrome-stream-only surface.
3. **incoherent control** (θ=0, same γ) folded in (the §3 template, generalized to the full mix).

### 7.4 Epistemic status (METRICS.md ladder)

The §7.1 column-4 observable predictions are **(b) prediction bands** — a miss is a finding. The exact-DM
checks + closed-form mechanism algebra + WG-vs-qutip + stim Clifford slices are **(a) exact**
zero-tolerance. The 0c gate thresholds are **(c) gates**. The "full-mix teacher faithful" verdict stays
**PROVISIONAL** (convergence + independent oracles), reportable + usable for go/no-go, nothing built on it.
