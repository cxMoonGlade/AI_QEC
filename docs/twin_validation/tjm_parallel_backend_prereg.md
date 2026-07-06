# TJM parallel backend — theory-first grounding + pre-registration (2026-07-06, DESIGN FOR REVIEW)

**User ask:** add a PARALLEL trajectory backend ("TJM") next to the existing MCWF-on-MPS leakage carrier, check
equivalence with the existing MPS arm, without touching the usable pipeline. **Grounding (close-read, notes
committed):** `sander_computational_regimes_mps_trajectories_2606.13779.md` (the cost-decision framework),
`sander_tjm_tensor_jump_2501.17913.md` (TJM), `froehlich_tensor_jump_method_2607.01323.md` (cTJM, extended);
MPS-line map verified against `mps_forward.py` / `sv_sampler.py` (file:line cites in the notes).

## 0. The honest grounded verdict (theory-fix; read BEFORE the plan)
1. **Our carrier is ALREADY an MCWF-on-MPS method** — with an *exact channel-resolved* unraveling: 1-site Kraus
   sampling of the exact `exp(L/4)` WG slice (zero within-slice error, bond-preserving), Born-sampled stabilizer
   parities with the √E_s POVM. In the papers' own taxonomy we are a "Kraus-insertion" unraveling — **named but
   never benchmarked** by them (2606.13779 §IV.B).
2. **TJM's three innovations target a continuous multi-site H₀** (dynamic TDVP no-jump propagation, Strang O(dt³)
   splitting, sampling-MPS reuse). Our within-cycle generators are purely 1-site ⇒ TDVP degenerates to exact 1-site
   exponentials; adopting TJM's dt-split unraveling would **replace an exact finite-width slice channel with a
   dt→0-convergent approximation** (TJM equivalence holds only in the double limit dt→0, N→∞; Thm 3 of 2501.17913).
3. **cTJM's quantitative gains are qubit-Pauli-conditioned** (P†P=1 ⇒ state-independent hazards, precomputed jump
   vectors, projector/analog variance theorems). WG leakage jumps (g|1⟩⟨2| etc.) are non-Hermitian/non-unitary ⇒
   **every claimed variance/bond/bookkeeping advantage evaporates** on our noise (froehlich note, applicability).
4. **Mid-circuit projective measurement + record conditioning — our defining workload — is absent from all three
   papers.** Their equivalence/variance results are single-time observables; nothing covers multi-time syndrome
   records.
5. **The measured bottleneck of our MPS line is not the unraveling at all**: it is the serial pure-Python per-op
   quimb loop (~70–90 quimb calls/round/shot, launch-bound at d3 ~1 s/shot; d5 χ=64 ~104 s/shot after the gesvd
   fix, residual = per-op overhead + serial shots — `mps_forward.py:311-349` docstring: d5/d7 production infeasible
   without the deferred **batched-shot** work). TJM shares nothing across trajectories ⇒ does not touch this.
6. **What the papers genuinely give us:** (G1) the **(α, κ) pilot decision protocol** (2606.13779 §V.A — bond
   inflation α and sampling inflation κ measured jointly; decision boundary κ vs α³ in our thread-limited regime;
   "reduced trajectory bond dimension does not automatically imply reduced total cost"); (G2) the **projector-style
   unraveling** idea as a bond lever — requires a non-Pauli analogue first (research-grade); (G3) the **bond-2 MPO
   for a·1+b·P operators** (cTJM §IV.C) — a direct candidate for our stabilizer √E_s apply, which is THE only
   bond-growing/truncating op in the whole trajectory; (G4) citable N-convergence theorems (σ_F ≤ 2/√N, any norm,
   size-independent) for certification budgets.

## 1. Registered plan (three separately-gated items; NOTHING touches the existing arm)
**P-TJM0 — the parallel arm + pilot (the user's ask, built to DECIDE not to presume).**
New sibling module (e.g. `forward/scalable/tjm_forward.py`), consuming the SAME upstream objects
(`RunSpec`, `XZZXSchedule.with_within_cycle_streams`, `build_within_cycle_leak`, `marshal_within_cycle`,
codestate builders, `_arm_d2`/√E_s/terminal instrument semantics — the integration contract in the MPS-line map)
and emitting the SAME `ShotSet` layout. Its between-measurement segment runs the TJM-style unraveling (Strang-split
1-site effective-H no-jump factor `D` = exact local contraction + norm-loss jump decision + single-site jump apply);
the measurement/readout layer is grafted UNCHANGED from our carrier (the papers do not cover it). `MpsLeakageForward`
is not modified; all existing tests must stay green.
- **Equivalence gates (registered; "全等" = distributional, never per-trajectory):**
  - E1 (a) *channel gate*: per within-cycle slice, the TJM arm's ensemble map must converge to the exact WG
    `exp(L/4)` channel with the declared O(dt²)/window bias → dt-halving sweep shows the slope; finite-dt EQUALITY
    with the exact-Kraus arm is NOT asserted (it would be false by construction).
  - E2 (a/b) *record gate at full χ*: `{det,obs}` statistics vs the exact QutritDM `record_oracle` (sub-register,
    existing seam) and vs the existing MPS arm at matched N — agreement within the σ_F ≤ 2/√N MC budget +
    two-sample record test; disagreement beyond MC error = generator-matching bug (stop, fix, not a regime effect).
  - E3 (c) *ledger*: per-arm discarded-weight books (`MpsTruncationLedger`) kept separately; no bond claim imported
    from the papers.
- **Adoption gate (the (α,κ) pilot, registered):** N_pilot trajectories per arm under identical conditions →
  measure (α, κ); the TJM arm is adopted ONLY if it beats the exact-Kraus arm on the joint κ·α³ boundary at matched
  accuracy. **Registered prediction (b): on our 1-site-generator + measurement-heavy workload the TJM arm TIES OR
  LOSES (κ·α³ ≥ 1).** A win is a finding (and immediately valuable); a loss closes the question with evidence and
  the arm is kept as a certified alternative unraveling, not the default.
**P-OPT1 (higher expected yield, orthogonal): bond-2 MPO for the √E_s stabilizer apply** — replace the dense 3^w
`gate_(contract='nonlocal')` with the a·1+b·P̃ bond-2 MPO form (G3) on the SAME arm; gate: bit-identical record law
(seed-matched shots) + measured wall/χ effect. Class (b) prediction: neutral-to-positive; it attacks the only
truncating op.
**P-OPT2 (the actual d5/d7 unlock, already the repo's own deferred item): batched-shot execution** — wave-style
batching of the deterministic op stream across trajectories (the dense CUDA kernel already does W=1024 waves).
Out of TJM scope; registered here so the speed goal is attached to the lever the measurement actually points at.

## 2. Sequencing + discipline
P-TJM0 design doc → user review → build (new files only; `mps_forward.py` untouched) → E1/E2/E3 gates → (α,κ)
pilot → adoption decision recorded in this doc. GPU serial; every run a committed script; faithfulness protocol
(declared + bounded vs the DM oracle) binds the new arm exactly as it binds the old one. P-OPT1/P-OPT2 are
separate proposals — not started without their own go-ahead.
