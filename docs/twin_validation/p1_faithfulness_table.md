# P1 — faithfulness coverage table (DRAFT v1, 2026-07-06)

**The moat deliverable** (product spec P1): every mechanism × its INDEPENDENT oracle × the bounded generation error ×
the max register/distance demonstrated. Rule (`FAITHFULNESS_PROTOCOL.md`): declared + bounded before "done";
unbounded = STOP for any load-bearing use. Sources: repo-wide inventory (read-only recon 2026-07-06, 3-agent sweep;
every cell cites its evidence file). Status ∈ {bounded, partially, **UNBOUNDED**, todo}. This draft = the work plan;
each `→P1:` item is the remaining work to move the row to *bounded*.

| # | mechanism / component | independent oracle | demonstrated bound | max scale shown | status |
|---|---|---|---|---|---|
| 1 | Mechanism catalog M0–M34 (Pauli/readout/damping/coherent) | hand-typed operator refs (8 coherent mechs) + analytic Kraus | operator ≤1e-12, unitary ≤1e-10, 1−F_e ≤1e-6; wrong-axis controls ≥1e-3 (`test_m6…m22` tier) | 1–2q channel objects; deployed on d3-XZZX 17q | partially — →P1: bound the DEPLOYED-register composition, not just the 1–2q object |
| 2 | Axis-1 joint-Lindbladian assembler (ZZ/T1/T2 coupled substep) | QuTiP + scipy Liouvillian/expm (3 independent refs) | superop <1e-13, Kraus TP ≤1e-12 (`test_joint_lindbladian`) | 5q dense substep (D=32) | **bounded** |
| 3 | QutritLeakageTeacher (WG coherent |1⟩↔|2⟩ + seep/heat) | hand-typed literature H refs + closed-form `leakage_channel_super` + **full-9q exact DM (P1-c)** | channel: H ≤1e-12, superop ≤2e-12, controls ≥1e-3; **record (P1-c 2026-07-06): full-9q R=1 wc-kernel marginals vs the SEQUENTIAL-measurement DM null, all 8 detectors z ≤ 2.54 @ N=1e6 (GATE PASS, `p1c_full9q_record_bound.py` hash f2cb1d5f…); multi-round R∈{2,3} = Gate-4 verdict cited (`p4a_verify_wc_gate4_ladder.py`)** | **d3 full register (9 qutrits), record level** | **bounded** (d3 record leg; logical entry report-only w/ declared POVM/backaction mismatches) |
| 4 | MCWF/MPS leakage carrier (W-B acceptance) | dense joint-L oracle (independent expm construction) + no-op anti-circular control | STRICT 1−F_e ≤1e-6, record/level TV ≤1e-6 (window dim ≤256); no-op carrier REJECTED (TV=1) | 3^5=243 window; d3 full = GROSS tier (TV ≤0.2, CI-capped) | partially — →P1: shrink the d3 GROSS tier or tile-decompose to STRICT windows |
| 5 | SeamTeacher family (tb_markov/backdrop/coherent seam) | D5 closed-form record-chain functionals | ≤1e-12 rel (r 1e-6, R 1e-4, T3 1e-9) (`test_carrier_seam_instrument`) | strip (2,2)=6q law; production (3,4) registered | **bounded** (registered strip) |
| 6 | B5 teachers (overrotation/damped-rotation/ZZ/corr-dephasing) | analytic Kraus defs + stim cross-check (marginals atol 0.01) | parity-path identity 1e-12; stim marginals 0.01 | rep-code d=5 (9q, R=2 exact) | partially — →P1: tighten the stim cross-check tier or declare it structural-only |
| 7 | RTNSource (telegraph latent) | exact telegraph closed forms + **sampled-trajectory pooled autocov (P1-b, `tests/test_source_closed_forms.py`)** | parameter forms exact; **P1-b: lags 1–5 \|z\| ≤ 0.30 vs A²e^(−2γl) at ~0.1–0.5% relative SE (M=3000×T=100, 5σ gate); γ-doubled negative control z=80–113; lag-0 = structural identity asserted exact (rtol 1e-12)** | timeline; 5q/d3_repz fixtures | **bounded** (timeline level; register deployment separate) |
| 8 | OneOverFDriftSource (RTN-sum 1/f) | analytic Lorentzian-sum autocov + **sampled-trajectory pooled autocov (P1-b)** | **P1-b: lags 1–5 \|z\| ≤ 1.4 vs Σv_k²e^(−2γ_k l) (~0.9% relative SE); γ-doubled negative control z ≥ 14.9 every lag; C(0)=A² exact (v_k=A/√K confirmed as declared)** + G6 rederivation cross-ref | timeline; 5q/d3_repz fixture R~12 | **bounded** (timeline level) |
| 9 | PhaseBurstSource | none today | property tests only | timeline, 3-site | **UNBOUNDED** — not accepted as a shared arm (teacher whitelist enforces); →P1 or park |
| 10 | TemporalStormSPPSource (2-state HMM) | exact 2-state Markov closed forms | stationary/corr-length exact; empirical vs marginal atol 0.02 | timeline, 8000 cycles | partially — →P1: record-level liveness once wired to a fixture |
| 11 | Θ fan-out (shared latent → params) | closed-form algebraic identities (inverse maps rel 1e-12) | exact identities | parameter map; 5q fixture | **bounded** (as a map; physics anchoring of constants stays class (c) declared) |
| 12 | quantum_bath GKSL shared-bath carrier | 6 Rule-I GT checks (factorization/extraction/indep-boson/emission-ODE/crow_joynt) + OQuPy independent K (~5%) | 1e-10…1e-6 per check | 2 data + 2 ancilla + 1 mode (exact DM, CPU) | **bounded** (feasibility scale) |
| 13 | Readout/reset instrument (MA(1)) | a-exact closed form μ=0.0149, p_ij(lag1)=μ, lag≥2=0 | exact + from-scratch cross-check; P0 P5 band ±20% live | 5q/d3_repz records R~12 | **bounded** |
| 14 | `records_to_dem` reduction (P0, NEW) | planted-parameter record law + **the teacher's EXACT enumerated record law (P1-a, `p1a_dem_reduction_bounds.py` hash 8d0032ee…)** | planted recovery ≤4e-3; roundtrip >0.999; **P1-a MEASURED bounds (d3_repz R=4, Θ(0)+64 trajectories): L0 misattribution ≤2.0e-2 on final:z12; isolated-eps ≤2e-2 on all no-L0 columns EXCEPT `delta:z12:round(R-1)` where eps≈0.97 — a pure DOUBLE-fault class (last-round ancilla × q2-final, closures cancel) the declared rule misses at mass ~1.5e-4; clustered-SE design effect DE(spt=200)=1.64–1.78 ⇒ SE understatement ×1.33** | 8-detector d3 fixtures, exact law | **bounded** (numbers above ARE the declared bound; L0-rule refinement — add the last-round delta column — optional, ~1.5e-4 mass-weighted) |
| 15 | `CoupledCycleTeacher` end-to-end {det,obs} | composite: joint-L (row 2) + C-10 closed-form rates + off-source identity atol 1e-14 | z1 rate closed form; x0 γφ-response band; emit byte-reproducible | d3_repz/5q (5q dense) R~12 | partially — →P1: single end-to-end record-law bound vs an independent enumeration at small R |

## P1 execution plan (session 2026-07-06/07 — registered before the runs)
- **P1-c (rows 3+15 flagship): full-9q R=1 record bound, wc-kernel vs exact DM.** The memory-lean oracle
  (`e8cee30`) demonstrated full-9q DETECTOR_MARG at 18.9 GiB/11 s — certify the SV within-cycle kernel's sampled
  record against it: per-detector marginal z ≤ 4 at N=1e6 (b), TVD reported; the LOGICAL entry is REPORT-ONLY
  (declared semantic mismatch: DM `logical_distribution` splits leaked mass evenly vs the kernel's biased-b terminal
  POVM — class (c) caveat, proper terminal-POVM DM leg is a follow-up). MODEL MATCHING is load-bearing: the kernel
  arm is `sv_traj_d3_wc` (within-cycle; driven per `p4a_verify_wc_gate4_ladder.py::kernel_hist`), NEVER the lumped
  `sample()` path, because the DM probe runs the within-cycle model. Existing Gate-4 verdict (TV(SV-MC, DM) at
  R∈{2,3}, 4 arms, 1/√N + positive controls, `p4a_verify_wc_gate4_ladder.py`) is CITED for the multi-round leg —
  reused anchors get their verdict read, not re-run.
- **P1-a (row 14, the P0 debts):** bound the declared L0 rule (exact P(obs=1 | single-detector fault class) from the
  dense record law — the d3_repz exact tables) + the clustered-SE design effect (exact between-trajectory variance
  from sampled per-trajectory exact laws) → numbers into the `records_to_dem` diagnostics defaults.
- **P1-b (rows 7/8/10):** quantitative PSD/autocov closed-form tolerance tests for RTN / OneOverF / TemporalStormSPP
  (CPU unit tests vs the declared Lorentzian(-sum) / 2-state-Markov forms).
- **Row 6:** declare the stim cross-check tier structural-only (doc edit). **Row 9 (PhaseBurst):** PARKED — fence =
  the teacher whitelist rejects it as a shared arm (`MEMORYFUL_SHARED_SOURCES`); unparked only with its own oracle.
- **Rows 1/4 PARKED with fences named:** row 1 (deployed-register composition bound) waits for P2's wiring (same
  register plumbing); row 4 (W-B GROSS→STRICT tiling) is a standalone engineering item — both stay declared-partial,
  never silently promoted.

**P1-c outcome note (2026-07-06):** the pre-run review's D1 was empirically vindicated — the ISOLATED per-detector
DM marginal (the residual-② probe flow AND `dm_oracle.py`'s DETECTOR_MARG answer semantics) differs from the
SEQUENTIAL-measurement marginal the kernel actually samples by up to **2.1e-4** (zero on detectors with no
non-commuting predecessors; leaked-sector non-commutativity at b=0.9). Gating against the isolated null would have
false-failed ≥3 detectors at 4.7–6.6σ. ⇒ the `dm_oracle` anchor's DETECTOR_MARG semantics need either the
sequential computation or a loud declaration (certify-seam follow-up chip). Also recorded: 4 of the 8 real-patch
stabilizers are pure-Z boundary checks.

**P1-a outcome note (2026-07-06):** the registered eps ≤ 5e-3 band MISSED on 4 columns — the miss is the finding:
isolated last-round-delta patterns are pure DOUBLE-fault classes (single faults cannot produce them), and the
z12-column one carries obs≈0.97 (its closure-cancelling partner is exactly the obs-flipping q2-final readout).
The declared L0 geometry rule is therefore incomplete for `delta:z12:round(R-1)` at double-fault order — bounded
at ~1.5e-4 mass; refinement optional. B2 in band: DE(spt=200)=1.64–1.78 (SE ×1.33).

**Aggregate honest picture (updated 2026-07-06, end of the P1 session slice):** **9/15 bounded** (rows 3, 7, 8, 14
promoted this session by P1-c/P1-b/P1-a), 5/15 partially (rows 1, 4, 6, 10, 15 — rows 1/4 parked with fences named,
row 6 declared structural-only, rows 10/15 next-slice items), 1 UNBOUNDED (PhaseBurst — correctly fenced off the
shared arm by the teacher whitelist). P1-b test file `tests/test_source_closed_forms.py` (6 tests, 26 green with the
existing suite) awaits mainline-commit confirmation. No row is silently unbounded-but-load-bearing; the two P0-introduced declared-not-yet-
bounded items are row 14's L0 rule + clustered-SE convention. **P1 exit criterion:** every load-bearing row bounded
or explicitly parked with its fence named; the table lands in the README/positioning doc as the coverage artifact.
