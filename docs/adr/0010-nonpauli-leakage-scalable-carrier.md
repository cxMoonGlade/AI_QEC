# ADR 0010 — Non-Pauli (leakage) scalable carrier: quimb MCWF-MPS forward + LPDO floor

## Status

**Accepted (decision 2026-06-21, user: "carrier-first, full force").** Advances the ADR 0008
charter for the **leakage / non-Pauli axis specifically**. Built on a 3-agent parallel explore
(representation+truncation theory / geometry+χ-cost+library / integration+certification), reports
archived in the session record. Theory-first: this decision + the constraint ledger + the
certification ladder are fixed BEFORE any carrier code. Epistemic classes per METRICS.md are tagged
throughout.

## Simulator-product boundary amendment (2026-07-14)

This ADR is retained as historical design provenance and is **partially superseded**:

- The old XZZX thin-strip driver remains in `legacy/qec_twin/forward/scalable/` and is not
  distributed. The installed 1D replacements are the restricted Axis-1 MCWF/MPS and QT/MPS
  execution surfaces under `error_coupling_simulator.frontend`; they are finite-step verification
  paths, not production-scalable, universal full-record, or full-`d×d` completion.
- The full-`d×d` carrier decision moved to the single-wire 2D PEPS line in ADR 0011.
- The LPDO/Bayes-floor half of this ADR belongs to downstream decoder/headroom analysis. Its code
  remains under `legacy/qec_twin/audit/`; it is not shipped and is not a simulator certification
  rung.
- The core Axis-2 classical stochastic record-memory service is unaffected by this amendment:
  replayable finite-RTN timelines (including the finite-band 1/f approximation), `Theta` fan-out,
  and matched-marginal controls. This is not a quantum-bath or CP-divisibility claim.

The body below records the 2026-06-21 decision as made; current product routing is governed by this
amendment, ADR 0011, and `docs/SIMULATOR.md`.

## Context

- **The pivot.** The exact `3^n` qutrit state-vector / `3^n×3^n` density matrix is **feasibility-only**:
  d3 DM = 6.2 GB (fits); d5 SV = 13.5 TB, d5 DM ≈ 10^23 GB (dead); d7 astronomically beyond. The
  d5/d7 surface-code simulator (the end goal — docs/SIMULATOR.md) cannot
  run on `forward/exact`. The DM-based Bayes floor (`audit/bayes_floor.py`) made this concrete: correct
  but slow, and a d3 dead-end.
- **Leakage is NOT DEM-reducible** (synthesis memo; 2603.18457 exclusion). ADR 0008's C2 outcome picked
  **C1 = DEM/HMM-bulk + window-exact coherent corrections** as the carrier for the **Pauli/coherent
  axis** — that bulk **structurally cannot carry leakage** (no `|2⟩` level; it sums Pauli mass). So the
  leakage axis needs its **own** carrier. This ADR records it; it **extends, does not overturn**, ADR 0008.
- Speed and scale are the same lever = a tensor-network carrier (area-law locality ≪ the full DM).

## Decision

1. **Engine: adopt `quimb`** (GPU via jax/torch/cupy; native arbitrary `phys_dim=3` qutrit; autodiff via
   `TNOptimizer` → satisfies ADR 0008 **R-GRAD**; MPS + MPO/LPDO; custom gate/Kraus application with
   `max_bond` truncation). Do **not** hand-roll MPS in `sv_traj_d3.cu` (months to reproduce quimb on GPU).
   Integration is low (fits the existing torch-c128 stack).
2. **Two carriers, two roles** (the load-bearing finding — they are different mathematical objects):
   - **Forward (data generation) = qutrit MCWF-on-MPS.** Pure-state quantum trajectories, each an MPS;
     WG leakage Kraus-sampled on the dim-3 physical leg; ensemble mean = the exact mixed evolution. The
     exact MPS lift of the project's existing dense MCWF and of **Manabe–Suzuki–Darmawan (arXiv:2308.08186)**
     — the one published large-d *leakage* TN simulator (snake ordering; χ=4/8/16 at 3×d/5×d/7×d; χ
     **constant in d**, area law; quantifies that the incoherent GTA over-predicts LER **>3×** — the reason
     to carry coherence faithfully). Cheap (~χ, not χ²); positivity trivial (pure states).
   - **Bayes floor = locally-purified MPDO / LPDO** (`ρ = X X†`, positivity structural). The floor's
     `P(f|s)` is a property of the **syndrome-conditioned MIXED state**; a single trajectory gives a sample
     from `P(s)`, **not** `P(s,f)`. **#1 architecture trap: never compute the floor from trajectories.**
3. **The d3 DM stays as the certification ORACLE** (`forward/exact/qutrit_dm.py` + `audit/bayes_floor.py`).
   Its faithfulness is established **component-wise** by the #11 L1 independent lane (vs the raw `.stim` +
   a from-scratch oracle — schedule byte-identical, leak dynamics |2⟩(R) to 1.4e-15, WG slice exp(L/4) to
   1.75e-13, ⟨S⟩/logical/detectors vs stim; the `1.5e-18` is the parsing/geometry cert, NOT a
   DM-output-distribution-vs-circuit residual — the leakage is INJECTED by our WG model, so there is no
   external circuit-leakage distribution to certify against). It is the only exact ground truth; the
   carrier is the scaling engine, not a replacement of the oracle.
4. **Geometry: snake (boustrophedon) along the SHORT lattice dimension.** Thin-strip (w×d) → χ small and
   constant in d. **Phasing: thin-strip first** (feasible d3→d7, KB–MB memory); **full d×d deferred** (a
   single MPS needs χ~exp(d) — dead at d7; full-square needs boundary-MPS, a genuine research risk).

## Design — load-bearing points (detail in the explore reports)

- **Truncation error (A).** Per-cut discarded weight `ε_cut = Σ_{i>χ} σ_i²`, with `‖ψ−ψ_χ‖² = ε_cut`
  (**class (a)**, Schmidt identity); accumulates `1−F ≤ Σ_t ε_cut^{(t)}`. **Honest caveat:** this bounds
  the **state**, NOT the LER/floor. Closure = certify the **`ε ↔ (LER-error, floor-error)` map vs the d3
  DM oracle** (the rigorous version of 2308.08186's convergence test). **Carry two ledgers, never merged:**
  (i) discarded-weight (state, class a); (ii) d3-certified ε↔error map (class b at d3, class c extrapolated
  above). Any coherence-dropping simplification is additionally bounded by Wood–Gambetta `C_L ≤ 2√(L(1−L))`
  — the recommended qutrit-native carrier has *zero* such error (carries `C_L` exactly).
- **Positivity (A).** MCWF (pure) + LPDO (`XX†`) are structurally PSD under truncation. **Plain-MPO
  truncation breaks positivity → `P(s,f)<0` → corrupted floor** (a silent toy-generator). The floor MUST
  use LPDO, never a plain MPO.
- **Integration (C).** CLAUDE.md's "backend-agnostic" is **aspirational, not true today**. Three implicit
  contracts must be made **explicit Protocols**: `ForwardLaw` (calibration/knobs bind to concrete
  `RepCodeForward`), `PathJointEvaluator` (`bayes_floor.py` hardwires the DM — spec'd in p7b §3, never
  built), `ShotSet` sampler. The **channel object (`StinespringChannel`) + do() ARE genuinely agnostic**
  (the `(t,i)→Kraus` field-callable is the one working seam). The `bayes_floor` refactor = **pure
  relocation + one Protocol** (DM bodies → `DMPathEvaluator`; the existing `tests/test_bayes_floor.py`
  L1/L2/L3/L6 are the bit-identical regression guard). **Reuse:** within-cycle marshalling + the load-bearing
  DD-echo frame (`sv_sampler.py`), the WG leakage channel (`channels.py`/`qutrit_teachers.py`), the parser
  (`xzzx_parser.py`), the seam/POVM conventions, and `forward/scalable/pins.py` + `CarrierErrorAccounting`
  (directly the d5/d7 oracle-free internal checks).

## Constraint ledger (carrier invariants + a falsifying test each — before building)

| # | Invariant | Falsifying test (must FAIL LOUDLY) |
|---|---|---|
| C1 | CPTP per channel: `‖Σ K†K − I‖ < 1e-12` | non-CPTP Kraus → residual trips; MCWF mean diverges from DM |
| C2 | Floor conditional-state positivity `ρ_s ⪰ 0` | truncate a plain MPO-ρ → negative eigenvalue caught (the LPDO-vs-MPO discriminator) |
| C3 | Probability semantics (p7b L6): `0≤P(s,f)`, `P(s,0)+P(s,1)=P(s)`, `Σ_s P(s)=1` | positivity-broken ρ_s → `P(s,f)<0` / residual >1e-9 fails |
| C4 | Leakage coherence carried: `C_L>0` iff `θ>0` | coherent arm `C_L` vs the dense channel to truncation tol; `C_L=0` only at θ=0 |
| C5 | Apply EVERY physical gate incl. per-round transversal X/Y DD echoes (FAITHFULNESS ledger #1) | drop echoes → leakage inflates 10–40× vs d3 oracle, caught at certification |
| C6 | MCWF-exactness: ensemble mean = exact DM to `O(1/√N)` | systematic offset beyond `O(1/√N)` ⇒ kernel/contraction bug ⇒ halt |
| C7 | Truncation convergence (no drift, FAITHFULNESS #7): refine ε ⇒ floor/LER converges | `F^χ` drifts monotonically as ε↓ ⇒ not converged ⇒ STOP |
| C8 | Zero-noise/zero-truncation exactness: ε→0 reproduces the dense DM bit-for-bit at d3 | mismatch >1e-10 at θ=g=0, large χ ⇒ carrier bug |

## Certification (the rung ladder, C; FAITHFULNESS rule I — independent ground truth)

- **Rung 0** — channel level: Choi distance `‖J_carrier−J_exact‖_F ≤ 1e-10` + PTM match + CPTP residual ≤ 1e-12. **(a)**
- **Rung 1** — d3 forward distribution vs DM-exact, ALL three metrics: TVD over the (s,f) joint, forward KL
  (`nll.joint_kl`, the learner-native object), per-detector marginals. Pass: ≤1e-10 at exact-grade χ; else
  the declared ε_log band (registration-grade SE/10 ≈ 3e-6), logged in `CarrierErrorAccounting.eps_log`,
  never folded into B_carrier. **(a)** at floor / **(b)** at finite χ.
- **Rung 2** — d3 Bayes-floor vs DM: `|F_carrier(R) − F_DM(R)| ≤ 3·MC-SE` + the L1 from-scratch enumerate
  anchor at R=1 + the L6 sanity. **(a)** estimator + honest band.
- **Rung 3** — χ(accuracy) convergence curve at d3 (TVD/KL/|ΔF| vs χ, anchored to DM); a χ* exists below the
  rung-1 threshold; monotone. This licenses the d5/d7 self-consistency. **(b)**
- **d5/d7 — oracle-free internal checks only** (certification STOPS being external here): CPTP residual;
  `pins.py` structural pins (Pauli-ablation ⇒ R_k==1, zero-seam exactness, unital-diagonal ⇒ R_k==1);
  χ-convergence self-consistency (the L2 no-drift analog — certifies *convergence in χ*, NOT correctness).
  **Every d5/d7 distributional claim is PROVISIONAL** (METRICS.md provisional corollary): reportable +
  usable for go/no-go gating, but NOTHING may be built on it as a premise.

## Alternatives considered (rejected, with reason)

- **Build our own MPS/LPDO in CUDA** — months re-deriving MPS/SVD/2D-contraction; reinvents quimb; GPU-first
  means *run on GPU* (quimb does), not *write the kernels*.
- **dMLE-style probability-level TN** — no coherent slot (sums probabilities, not amplitudes); ADR 0008
  already ruled it inadmissible as carrier (mandatory as a baseline arm).
- **Plain MPO-ρ for the floor** — truncation breaks positivity → corrupted floor.
- **cuda-qx TN simulation** — qubit-only physical dim; cannot carry `|2⟩` leakage (it is the project's TN
  *decoder*, not a carrier). **Stim** — Clifford/Pauli-only; leakage is outside the computational subspace
  and not a Pauli channel (authors' own statement). **TeNPy** — no first-class GPU (disqualified by R-GPU).

## Consequences / open risks (honest)

- **New dependency: quimb** (+ its jax/torch GPU backend). Must pass a de-risk smoke test (GPU + qutrit MPS
  + autodiff + a WG-leakage Kraus) in our WSL2/5090 env BEFORE the full build.
- **d7 full-square leakage-forward is a research risk** (thin-strip d7 is fine). Phasing: thin-strip first.
- **The floor's exact enumeration dies above d3** (2^(R·24/48) syndrome space) → becomes a per-shot
  conditional bracket (already the p7 prereg's S1).
- **Above d3 there is no external certification** → PROVISIONAL (see Rung d5/d7).
- **LPDO has no efficient locally-PSD canonical form; the Kraus/purification bond may not stay bounded**
  under the WG leakage steady-state (De las Cuevas 1512.05709 / 1404.4466; the LPDO critical-point result
  2312.02854). Profiled-not-assumed; the C7 drift tripwire is the guard.

## Build plan (M3 — ≥3 disjoint agents, GPU-serial)

8a quimb de-risk smoke test (GPU+qutrit+autodiff+leakage) · 8b backend-agnostic interface extraction
(`ForwardLaw`/`PathJointEvaluator`/`ShotSet`; `bayes_floor`→`DMPathEvaluator`, tests as guard) ·
8c quimb MCWF-MPS forward backend · 8d quimb LPDO floor backend · 8e certify vs d3 DM (rung ladder) +
un-led reviewer + from-scratch red-team. commit-gate on every `src/` addition.

## Epistemic-status audit

Truncation identity (ε_cut) **(a)**; χ-scaling/cost projections + the ε↔error map **(b)**; the engine/
representation/geometry **decisions** and τ-style thresholds **(c)** gates; all d5/d7 distributional
results **PROVISIONAL** until (impossibly) an external oracle exists — they never become premises.
