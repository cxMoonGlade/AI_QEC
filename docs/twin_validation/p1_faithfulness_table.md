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
| 3 | QutritLeakageTeacher (WG coherent |1⟩↔|2⟩ + seep/heat) | hand-typed literature H refs + closed-form `leakage_channel_super` | H ≤1e-12, U ≤1e-10, superop ≤2e-12; wrong-physics controls ≥1e-3 (`axis1_qutrit_leakage_certification`) | 1–2 site channel; deployed d3-XZZX 17-site MCWF | partially — →P1: end-to-end d3 RECORD bound vs DM oracle beyond R=1 sub-register (cf. residual-② C2/C4) |
| 4 | MCWF/MPS leakage carrier (W-B acceptance) | dense joint-L oracle (independent expm construction) + no-op anti-circular control | STRICT 1−F_e ≤1e-6, record/level TV ≤1e-6 (window dim ≤256); no-op carrier REJECTED (TV=1) | 3^5=243 window; d3 full = GROSS tier (TV ≤0.2, CI-capped) | partially — →P1: shrink the d3 GROSS tier or tile-decompose to STRICT windows |
| 5 | SeamTeacher family (tb_markov/backdrop/coherent seam) | D5 closed-form record-chain functionals | ≤1e-12 rel (r 1e-6, R 1e-4, T3 1e-9) (`test_carrier_seam_instrument`) | strip (2,2)=6q law; production (3,4) registered | **bounded** (registered strip) |
| 6 | B5 teachers (overrotation/damped-rotation/ZZ/corr-dephasing) | analytic Kraus defs + stim cross-check (marginals atol 0.01) | parity-path identity 1e-12; stim marginals 0.01 | rep-code d=5 (9q, R=2 exact) | partially — →P1: tighten the stim cross-check tier or declare it structural-only |
| 7 | RTNSource (telegraph latent) | exact telegraph closed forms (flip prob, autocov) | exact (pytest.approx); byte-replayable | timeline (no register); 5q fixture | partially — →P1: PSD-level check vs declared Lorentzian |
| 8 | OneOverFDriftSource (RTN-sum 1/f) | analytic Lorentzian-sum PSD (structural checks only today) | psd>0, monotonic ends (structural) + G6 rederivation cross-ref | timeline; 5q/d3_repz fixture R~12 | partially — →P1: quantitative PSD/autocov tolerance test |
| 9 | PhaseBurstSource | none today | property tests only | timeline, 3-site | **UNBOUNDED** — not accepted as a shared arm (teacher whitelist enforces); →P1 or park |
| 10 | TemporalStormSPPSource (2-state HMM) | exact 2-state Markov closed forms | stationary/corr-length exact; empirical vs marginal atol 0.02 | timeline, 8000 cycles | partially — →P1: record-level liveness once wired to a fixture |
| 11 | Θ fan-out (shared latent → params) | closed-form algebraic identities (inverse maps rel 1e-12) | exact identities | parameter map; 5q fixture | **bounded** (as a map; physics anchoring of constants stays class (c) declared) |
| 12 | quantum_bath GKSL shared-bath carrier | 6 Rule-I GT checks (factorization/extraction/indep-boson/emission-ODE/crow_joynt) + OQuPy independent K (~5%) | 1e-10…1e-6 per check | 2 data + 2 ancilla + 1 mode (exact DM, CPU) | **bounded** (feasibility scale) |
| 13 | Readout/reset instrument (MA(1)) | a-exact closed form μ=0.0149, p_ij(lag1)=μ, lag≥2=0 | exact + from-scratch cross-check; P0 P5 band ±20% live | 5q/d3_repz records R~12 | **bounded** |
| 14 | `records_to_dem` reduction (P0, NEW) | planted-parameter record law (exact odd-parity residual discriminated from 1st-order, gap 1.44e-2 ≫ 4e-3 tol) | planted recovery ≤4e-3; pymatching roundtrip >0.999 | 8-detector d3 fixtures | partially — →P1: bound the **declared L0 rule** + the **clustered-SE deviation** vs the exact record law (both declared, neither bounded yet) |
| 15 | `CoupledCycleTeacher` end-to-end {det,obs} | composite: joint-L (row 2) + C-10 closed-form rates + off-source identity atol 1e-14 | z1 rate closed form; x0 γφ-response band; emit byte-reproducible | d3_repz/5q (5q dense) R~12 | partially — →P1: single end-to-end record-law bound vs an independent enumeration at small R |

**Aggregate honest picture:** 5/15 bounded, 9/15 partially, 1 UNBOUNDED (PhaseBurst — correctly fenced off the shared
arm by the teacher whitelist). No row is silently unbounded-but-load-bearing; the two P0-introduced declared-not-yet-
bounded items are row 14's L0 rule + clustered-SE convention. **P1 exit criterion:** every load-bearing row bounded
or explicitly parked with its fence named; the table lands in the README/positioning doc as the coverage artifact.
