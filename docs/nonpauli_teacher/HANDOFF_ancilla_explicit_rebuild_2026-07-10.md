# HANDOFF — ancilla-explicit sampling-arm rebuild (2026-07-10)

Resume brief for the surface-code TN carrier line after the **compiled-geometry
DM-PEPO carrier was closed as a findings package** (rung-1 first execution, 2026-07-10).
This doc is the entry point: current state → why the compiled carrier failed → the
rebuild plan → the concrete literature basis for each design decision → next actions.

Governing prior docs (still valid where cited): `pepo_engine_rung1_contract.md` (v4.3,
findings F-SEL-1 / F-REC-1 + the E1/E2/E3/loop-rank probe outcomes appended), the
`pepo_d5d7_carrier_prereg.md` (v2.5). Superseded direction: the compiled DM-PEPO
sampling arm.

---

## 1. CURRENT STATE (what is settled, what is committed)

**The compiled-geometry 2D density-matrix PEPO carrier is CLOSED.** It was built,
its engine CERTIFIED faithful, and then FALSIFIED at d3 by first execution. Both arms
failed:

- **F-SEL-1** (selective sampling arm, `born_sample_round`): √E_s Born-branch states
  are near-projected-stabilizer states with FLAT bond spectra; truncating per-bond to
  D=16 discards 29–70% of squared-σ weight → negative traces (C3 STOP). Adjudicated
  path (C): demote G1.1 to characterization; the record law carries on G1.2 +
  `terminal_readout_obs`.
- **F-REC-1** (nonselective record law, G1.2): sequential-null marginals go NEGATIVE
  (p_j(stab5) = −3.6e-3 on ~1e-3-scale marginals) → dp/bar ≈ **25–40 ≫ the 0.1 gate**.
  USER-adjudicated early stop at R=4/10 (the R=1..4 table is the finding evidence).

**Root cause (mechanism, [ours] with measured + theorem support):** the S10 compilation
**compiled away the ancilla qubits**, turning each stabilizer measurement from "four
2-qubit CZ gates + a **single-site** ancilla readout" into ONE **weight-4 multi-site
POVM** E_s on the 9-site data lattice — a rank-25 tensor-train insertion along a
plaquette path. That TT concentrates circuit-distributed correlations onto a few coarse
path bonds. The frozen feasibility number χ(1e-6)=16 was a **global single-cut**
quantity; it never bounded **per-bond** truncatability (the prereg's DECLARED S1
optimistic-proxy risk, now materialized).

**Terminal discriminator — the loop-closed rank probe** (gauge-independent, engine
E1-verified): on the D=64 lossless state, all six fat bonds have FULL loop-closed rank
(25/64) → **no lossless regauge to D=16 exists in this geometry**. Two-class structure:
4/6 bonds are 16-effective loop-closed (weight beyond 16 = 3e-6…4e-3 — where the LOCAL
pair spectrum charged 0.43–0.70), but 2/6 bonds (the FRESHLY-GROWN path bonds) are
genuinely heavy (0.29–0.58 beyond 16, flat past k=24). Even a full loop-update/FET build
would fix 4 bonds and still lose O(1) on the other two. **Adjudicated: the compiled
geometry is closed for the sampling arm and for record-law-at-bar.**

**What is CERTIFIED and RETAINED (not thrown away):**

- **The engine is E1-verified FAITHFUL** vs the exact QutritDM referee (dense equality
  **1e-15** through 4 forced-outcome branches at D_cap=64). The v4.3 truncation code
  (two-pass `svd_precut_bond` + metric-copy env bounding + greedy contraction) is
  correct — the trace collapse was REAL truncation error, not a bug.
- **50/51 pytest green** (1 registered F-SEL-1 skip). G1.0 codestate + all units +
  KILLERs pass.
- **The G1.9-pre measured bar = 4.8e-4** (Weyl floor binds; registered).
- All the machinery — layout/grid transform, plaquette paths, the exact stabilizer-TT,
  the NTU truncation, boundary-MPS caps contraction, the DMPathEvaluator referee wiring,
  the certification harness — stays valuable as the **record-law / oracle substrate** and
  as reusable components for the rebuild.

**Commits (docs on `Dev-F`, all pushed to the working branch):**
- `79766e9` — engine + tests (the findings package): src/error_coupling_simulator/carrier/pepo/ + test_pepo_rung1 + skip_allowlist + CODE_MAP/code_status (pepo pkg marked ARCHIVED with the closure note).
- `9af516f` — (A)-probe outcome (no lossless regauge).
- `2eccc1f` — F-REC-1 registered.
- `659f305` — F-SEL-1 adjudicated (option C + loop-update probe).
- `61a9c22` — F-SEL-1 theory-fix update (engine exonerated).
- `8ecaa81` — contract v4.3 first-execution amendments + F-SEL-1.
- `9dfa37c` — G1.9-pre bar registered (prereg v2.5).

**Local-only evidence (gitignored `outputs/nonpauli_teacher/`):** all gate scripts +
runners + the probe scripts (`pepo_rung1_probe_*`) + logs
(`pepo_rung1_g12_*.earlystop-20260710.log`, `pepo_rung1_probe_loop_rank.log`, etc.).

**G1.8 (window calibration, oracle-side) is carrier-INDEPENDENT** — it runs on the exact
QutritDM, quantifies the S11 window-embedding bound for rung-2, and can be run any time
the GPU is free (its runner + measured-bar wiring are ready).

---

## 2. WHY THE REBUILD MIGHT WORK — the mechanism, grounded

**The fix is to NOT compile the ancilla away.** With ancilla explicit, each stabilizer
measurement is back to its native form: four 2-site CZ gates (each multiplies a bond by
the gate's small rank) + a **single-site** measurement (bond-dimension INERT — a
single-site operator changes no bond). The rank-25 multi-site POVM concentration
**never forms**. Entanglement enters only through 2-site gates, incrementally, and is
truncatable step-by-step — exactly the regime standard TN-QEC methods operate in.

**Deeper root cause (the survey sharpened this): the rank concentration is a
DOUBLED-WIRE (density-matrix) artifact.** The compiled weight-4 POVM was inserted as a
tensor-train along a plaquette path, and the density-matrix representation FUSES ket⊗bra
into one leg — so a bond-2 parity structure gets SQUARED up the path to the observed
rank 25/64. Three theorems make this precise and point the way out:
- **cTJM (Fröhlich et al., 2607.01323, Sec. IV.3):** any operator `a·I + b·P` (P a
  parity string on an arbitrary, possibly non-adjacent support) has an EXACT **bond-2**
  MPO, separation-independent. A stabilizer parity projector `(1±P̃)/2` is exactly this
  form. In a SINGLE-WIRE (pure-state) representation the check is bond-2 — the rank-25
  never arises; the squaring is purely the doubled-wire ket⊗bra.
- **TJM (Sander et al., 2501.17913, Eq. 40):** a SINGLE-SITE operator factorizes as
  `⊗_l D_l` and is **bond-INERT** on an MPS (the single-site restriction is load-bearing
  for the factorization). Ancilla-explicit ⇒ the measurement is single-site ⇒ collapse
  grows no bond. And the trajectory sum `ρ_N` is **positive-semidefinite BY CONSTRUCTION**
  (a sum of pure-state projectors) — it CANNOT hit the F-SEL-1/F-REC-1 negative-trace
  failure, which was a truncated-ρ artifact with no analogue in the trajectory picture.
- **Jaschke (1804.09796):** the representation taxonomy — MPDO (density-matrix MPO)
  SQUARES local+bond dims `(χ,d,χ)→(χ²,d²,χ²)` and does NOT preserve positivity under
  truncation (checking MPO positivity is NP-hard); QT (quantum-trajectory pure states)
  is the natural record-emitting carrier; LPTN/LPDO buys structural positivity at a Kraus
  index. The doubled-wire squaring we suffered is the generic MPDO cost, not a
  surface-code accident.

Two independent literature anchors confirm ancilla-explicit surface-code TN simulation
carries SMALL bonds:

- **Manabe–Suzuki–Darmawan (arXiv:2308.08186, NJP 2025)** — ancilla-explicit, qutrit
  leakage, pure-state trajectory MPS: bonds SATURATE with rounds (area law in circuit
  time, their Fig. 6); logical states need only χ=4/8/16 for 3×d/5×d/7×d. Their method
  is EXACTLY our sampling arm's target, at CPU-only scale far larger than our d3.
- **Darmawan–Poulin (arXiv:1607.06460, PRL 2017)** — full d×d PEPS, checks kept as
  LOCAL bond-2 face-tensor insertions (Eq. 6), boundary-MPS syndrome sampling at
  **χ_b=8** reproducing the exact 153-qubit (9×17) logical channel. Note: D-P uses the
  SAME single-layer B=A⊗A* doubled-leg representation we did — proving the representation
  is not the problem; the COMPILED PATH-TT geometry was.

**The gap our rebuild fills** (Manabe's own comparison table, verbatim): "the full 2D
tensor network handles geometry [D-P], the MPS handles dynamics/noise [Manabe] — but
neither does both at scale." Our conjunction — **2D geometry × multi-round noisy+leaky
dynamics × coupled/correlated records × oracle-bounded certification** — is the unfilled
intersection. This is the correct novelty framing (NOT "add PEPS to Manabe").

---

## 3. THE REBUILD PLAN — decisions + rung sequencing

### 3.1 Representation decision (the central choice)

Three candidate representations, with the literature verdict:

| Representation | What it is | Positivity | Repo infra | Verdict for the SAMPLING arm |
|---|---|---|---|---|
| **Pure-state trajectory MPS/PEPS** (Manabe) | state-vector of (d_q=3, χ); density matrix NOT carried, stochastic Kraus sampling per trajectory; a **trajectory IS a record sample** by construction | N/A (pure states) | **EXISTS** — `qec_twin/forward/scalable/{mps_forward,sv_sampler}` already does qutrit MCWF-on-MPS | **PRIMARY.** Ancilla-explicit, single-site collapse bond-inert, matches the task semantics (sample records, don't build ρ), reuses GPU machinery |
| **LPDO / LPTN** (Werner ρ=XX†) | locally-purified: physical + bond + Kraus indices; positivity STRUCTURAL; Theorem-7 trace-norm error bound | guaranteed by construction | none | deferred: heavier (bond + Kraus dims), 1D core needs snake/strip for 2D; the fallback IF pure-state trajectory sampling variance is intractable |
| **Density-matrix PEPO** (what failed) | fused d²=9 leg, single-layer Tr(ρΠ) | not guaranteed (the C3 problem) | the closed engine | RETAINED only as the record-law/oracle substrate at small scale; NOT the sampling carrier |

**Decision: the sampling arm is a pure-state trajectory carrier (Manabe-class).** The
density matrix is never formed; each Monte-Carlo trajectory (unitary gates + sampled
Kraus + single-site measurements) yields one syndrome+leakage record. This is the lightest
slice, reuses existing repo GPU MPS machinery, and its representation cannot hit the
F-SEL-1/F-REC-1 negative-trace failure (there is no truncated ρ to go non-PSD). The
record-law marginals come from the empirical trajectory ensemble, not a DM contraction.

### 3.2 Geometry decision

- **d3 (immediate):** the real 17-qutrit circuit (9 data + 8 ancilla) is quasi-1D
  enough for an **MPS snake** — this is Manabe's exact method at a scale (17 qutrits, few
  rounds) far below their demonstrated d=99 / d=19. **No 2D machinery needed for d3.**
- **d5/d7 (the real 2D build):** the snake MPS bond grows as χ^W in the width W=d, so
  full d×d needs a genuine 2D ansatz. Two literature-grounded routes:
  - **(2D-a) pure-state PEPS + boundary-MPS sampling** (D-P geometry mechanism, applied
    to trajectories): checks as LOCAL bond-2 face tensors, sample syndromes by
    boundary-MPS contraction at χ_b. D-P proved χ_b=8 exact at single-round/perfect-
    measurement; the OPEN part is multi-round noisy+leaky.
  - **(2D-b) iPEPO / tePEPO** (Dunham–Szymańska 2512.01781): only if a density-matrix 2D
    carrier is wanted for the record-law arm — supplies itrSU truncation + VUMPS/CTMRG
    contraction + FSA rules for stabilizer lattices (Table V, toric code). But tePEPO is
    Markovian-time-evolution machinery; our need is codestate + circuit syndrome
    extraction (tePEPO's own open-question 5 flags this distinction), so 2D-a is closer.

### 3.3 Rung sequencing (low-risk-first)

- **RUNG-A (fast, low-risk — DO FIRST): d3 ancilla-explicit trajectory MPS sampler.**
  Restore ancilla, snake-MPS, sample {det, obs} records, certify against our EXISTING
  exact QutritDM referee (the same 1e-15 oracle that E1-exonerated the old engine). This
  ALONE recovers the sampling arm and validates the whole approach at minimal cost.
  Manabe's own open-question 3 recommends exactly this ("replicate the thin-strip results
  as a validation step before moving to full 2D"). Reuses `sv_sampler` machinery.
- **RUNG-B (the real contribution): d5/d7 2D pure-state PEPS + boundary sampling.**
  Registered bet (predict-before-measure): does the 2D bond SATURATE with rounds (area
  law in circuit time)? Anchors: Manabe's 1D/quasi-1D saturation (Fig. 6) + D-P's 2D
  single-round χ_b=8 — the INTERSECTION (2D × multi-round) is unmeasured by anyone and is
  precisely what we register. **PRE-INVESTMENT RISK CHECK (Rudolph–Tindall 2507.11424):**
  our rotated d×d XZZX is the z=4 rotated-square (Willow) geometry whose small 4-site
  plaquettes build loop correlations rapidly (their boundary bond R~75 at L=15 vs R=1 for
  heavy-hex) — measure the BP-error ε_l (their Eq. 3-4, transfer-matrix loop eigenvalues)
  on our patch BEFORE committing the 2D build; a large ε_l says the boundary-MPS χ_b will
  be expensive and biases the geometry choice.
- **RUNG-C (novelty payload): coupled/correlated records** (the latent memory axis) on
  the validated carrier — the actual project mainline (notion-2 record memory), which the
  sampling arm exists to serve.

### 3.4 Scope-fence reopening (process note)

The ancilla-explicit rebuild REOPENS the S10/C10 compilation scope fence — this was
FLAGGED as a BLOCKER-grade ledger item in the ORIGINAL prereg review (the "ancilla-free
compilation missing from the ledger" finding → S10/C10). Reopening it is walking through
the door the review pre-registered, not overturning the prereg. A NEW registration
document (theory-first + full red-team contract-build) governs the rebuild.

---

## 4. LITERATURE BASIS (the concrete grounding — arXiv id + specific fact per decision)

**Personally re-read for this handoff (the load-bearing anchors):**

| Paper | arXiv | The specific fact / method the rebuild cites |
|---|---|---|
| Manabe–Suzuki–Darmawan (NJP 2025) | 2308.08186 | THE direct method anchor: ancilla-explicit qutrit-leakage pure-state trajectory MPS; bonds SATURATE w/ rounds (Fig. 6, area law in time); χ=4/8/16 logical states for 3×d/5×d/7×d; GTA overestimates LER >3× (why not Pauli-twirl leakage); SVD is the CPU bottleneck at d≥5 → GPU is our lever; open-Q3 recommends the d3-first validation |
| Darmawan–Poulin (PRL 2017) | 1607.06460 | THE 2D geometry + boundary-sampling anchor: full d×d PEPS, checks as LOCAL bond-2 face tensors (Eq. 6, NOT compiled path-TTs), boundary-MPS syndrome sampling O(LW·χ³) at **χ_b=8** = exact for 153 qubits (9×17); single-layer B=A⊗A* (same representation we used — proves geometry, not representation, was our bug); single-round + perfect measurement (the limit our multi-round rebuild extends) |
| Werner et al. (PRL 2016) | 1412.5746 | THE positivity fallback: LPDO ρ=XX† keeps positivity STRUCTURAL (dodges the C3/F-SEL-1 negative-trace failure entirely); Theorem 7 trace-norm error bound = the bounded-simplification language; but 1D core + no repo infra → the deferred fallback if trajectory variance is intractable |
| Dunham–Szymańska (2025) | 2512.01781 | tePEPO iPEPO (d²,D,D,D,D) 2D carrier: itrSU truncation (avoids re-gauging, O(d⁴D⁶η³)), VUMPS/CTMRG contraction, FSA rules for the toric code (Table V); Markovian-time-evolution machinery — its open-Q5 flags codestate+syndrome ≠ full time-evolution (why 2D-a beats 2D-b for us) |

### 4b. Full load-bearing basis (from the 6-cluster reading-note survey, workflow wtj9x7ga8)

The survey read ~44 TN/PEPS/QEC-TN notes across 6 clusters. The load-bearing subset
(the papers a rebuild registration MUST cite), grouped by which decision they anchor.
The three theorems in §2 (jaschke taxonomy, TJM Eq. 40 bond-inert, cTJM bond-2) are the
representation-decision core and are re-listed there.

**Representation decision (Q1 — DM-PEPO vs LPDO vs pure-state trajectory):**

| Paper | arXiv | Load-bearing contribution |
|---|---|---|
| Jaschke et al. | 1804.09796 | The taxonomy that SETTLES the menu: QT / MPDO / LPTN. MPDO squares dims + no positivity-under-truncation (NP-hard to check); QT = natural record-emitter; LPTN = structural positivity at a Kraus index. Caveat carried: **purity ≠ trajectory average** (arm-consistency check when the record law is derived from the trajectory ensemble). Anti-toy guard: a joint Lindblad `L=A+B` must NOT be split into independent `A,B` (drops `LρL†` cross terms) — same-substep couplings assemble into ONE generator. |
| Sander et al. (TJM, Nat. Commun. 2025) | 2501.17913 | THE core theorem: single-site operator ⇒ `⊗_l D_l`, **bond-inert** (Eq. 40); trajectory sum ρ_N is **PSD by construction**; MCWF↔Lindblad equivalence (Appendix A). The mechanism justification for "restore ancilla ⇒ single-site measurement ⇒ no bond growth." Repo's `mps_forward` is already this class. |
| Fröhlich et al. (cTJM) | 2607.01323 | The structural antidote: `a·I+b·P` (parity projector `(1±P̃)/2`) has an EXACT **bond-2** MPO, separation-independent (Sec. IV.3). Also: projector-unraveling suppresses trajectory entanglement at strong noise (bond-dim lever) — but ALL its variance gains are Pauli-conditioned (`P²=I`), so they do NOT transfer to our non-Pauli leakage jumps `g\|1⟩⟨2\|`; no mid-circuit measurement in scope (grafting Born-collapse is mechanically fine but its variance theory does not survive the collapse). |
| Werner et al. (LPDO, PRL 2016) | 1412.5746 | The positivity fallback for the RECORD-LAW arm if it stays density-matrix: ρ=XX† structural positivity; Theorem-7 trace-norm error bound = the bounded-simplification language. Deferred (1D core, no repo infra). |

**Geometry + sampling decision (Q2):**

| Paper | arXiv | Load-bearing contribution |
|---|---|---|
| Darmawan–Poulin (PRL 2017) | 1607.06460 | Full d×d PEPS, checks as LOCAL bond-2 face tensors (Eq. 6), boundary-MPS sequential-conditional syndrome sampling `q=Tr(P_{k+1}ρ_k)` at **χ_b=8** = exact (153q, 9×17). Single-round + perfect measurement — the ancestor of the closed carrier AND the geometry we lean on. Its follow-ups (1801.01879 linear-time decoder, 2403.08706 adaptation) share the machinery. |
| Rudolph–Tindall (GPU PEPS 2025) | 2507.11424 | THE 2D sampling engine: reverse-pass norm-cache + forward-pass sequential single-site-partition boundary-MPS sampling (with p/q-ratio, sample-KLD, importance-sampling quality gates) — the exact sampler for the pure-state trajectory arm on our planar lattice. **CRITICAL CAUTION for RUNG-B:** our rotated d×d XZZX IS the z=4 rotated-square (Willow) geometry whose small 4-site plaquettes build loop correlations RAPIDLY (boundary bond R~75 at L=15, vs R=1 for heavy-hex). The BP-error metric ε_l (Eq. 3-4, from transfer-matrix loop eigenvalues) is a PRE-INVESTMENT diagnostic to measure our patch's loop-correlation cost before committing the 2D build. |
| Piveteau et al. (TN decoding) | 2310.10722 | The ALTERNATIVE to ancilla-restore: SNAKING (linearize a high-degree node into a chain, truncate along it) as the documented complement for the weight-4 concentration; 3D-as-stacked-2D + MPS sweep-line for the multi-round geometry; Simple Update as loopy-2D truncation with NO canonical gauge — and its d≥11 breakdown (a scale warning). |
| Dunham–Szymańska (tePEPO 2025) | 2512.01781 | The 2D DM carrier IF the record-law arm goes density-matrix: itrSU truncation (O(d⁴D⁶η³)), VUMPS/CTMRG contraction, toric-code FSA rule table (Table V). But Markovian-time-evolution machinery; its own open-Q5 flags codestate+syndrome ≠ time-evolution — 2D-a beats 2D-b for us. |

**Truncation for the record-law DM arm (if kept):**

| Paper | arXiv | Load-bearing contribution |
|---|---|---|
| Dziarmaga (NTU) | 2107.06635 | The exact NN-cluster metric g — Hermitian, non-negative, **GAUGE-FREE** — replacing the gauge-arbitrary per-bond SVD that lost 29–58%. Gauge-independence is exactly the property the loop-closed rank probe found the D=16 cut lacked. Already implemented in the closed engine (carries forward). |
| Kilda et al. (iPEPO stability) | 2012.03095 | The loud warning: **D-sweep convergence is NOT a valid certification** for a DM-iPEPO arm (at J_y=1.5, D=3,4 converge but D=5,6 DESTABILIZE; spurious low-D steady states). The ε_Λ per-bond stationarity diagnostic (required <ε for EACH of the four Λ bonds). AND an INDEPENDENT argument FOR the rebuild: restore ancilla as PHYSICAL sites (larger local d²), not as bond dimension D — the instability is bond-D-specific. Cross-validate against the exact-Liouvillian referee (we have the 1e-15 exact-DM oracle), never D-sweep alone. |

**Coupled/correlated-records novelty axis (RUNG-C — the payload the sampling arm serves):**

| Paper | arXiv | Load-bearing contribution |
|---|---|---|
| Kam et al. (spatiotemporal Pauli processes) | 2603.05474 | The canonical construction for CORRELATED MULTI-ROUND noise as a positive classical trajectory distribution at surface-code scale (d=19): multi-time Pauli twirl → process-separable comb → TN with bond ≤ env-Liouville dim. Reference for the multi-round bond budget + the sampling-arm-as-trajectory-distribution decision; carries the pseudo-critical-avalanche bond-blowup caveat. (The other 6 coupled-records notes are stabilizer forward-sims / stat-mech threshold theory / syndrome-moment estimators — context, not representation anchors.)

**Net survey verdict:** the ancilla-explicit pure-state trajectory sampling arm has NO
direct published precedent (every QEC/surface-code TN paper in the corpus compiles the
ancilla away — 1607.06460 literally does the move that produced our rank concentration).
The rebuild deliberately departs from the dominant pattern; the departure is grounded
theorem-by-theorem (bond-inert single-site collapse, bond-2 parity, PSD-by-construction
trajectory sum), and the conjunction it enables (2D × multi-round × coupled × certified)
is the unfilled intersection Manabe's own comparison table names.

**One cheap early probe the survey surfaced (do before RUNG-A registration):** the cTJM
bond-2 parity-MPO insight (2607.01323 §IV.3) predicts that inserting the stabilizer
parity as a bond-2 MPO — rather than the rank-25 doubled-wire path-TT — collapses the
concentration. A single script (reuse the existing engine + exact referee) that inserts
the Pauli-parity part as bond-2 on the OLD DM geometry and measures the resulting bond
would independently confirm the "doubled-wire is the culprit" diagnosis and de-risk the
representation choice for near-zero cost. (Caveat: our biased-b leaked-readout `√E_s` is
NOT of the `a·I+b·P` form — the `|2⟩` weight `1−2b` breaks it — so this probes the
Clifford-parity part only; it is a diagnosis confirmation, not itself the fix.)

---

## 5. CONCRETE NEXT ACTIONS (in order)

1. **(DONE) Literature survey folded into §4b** — the load-bearing basis is registered.
2. **cTJM bond-2 diagnosis probe (cheap, ~1 script):** confirm the doubled-wire
   diagnosis by inserting the stabilizer Pauli-parity as a bond-2 MPO (cTJM 2607.01323
   §IV.3) on the OLD DM geometry vs the rank-25 path-TT, measure the bond. Reuses the
   committed engine + the exact referee. Near-zero cost, de-risks the representation
   choice. (Diagnosis only — the biased-b `√E_s` needs the trajectory picture for the
   full fix.)
3. **G1.8 opportunistic run** (carrier-independent, GPU-free window) → the S11 rung-2
   window-embedding bound. Runner + measured-bar wiring are ready.
4. **RUNG-A registration** (theory-first + contract-build): the d3 ancilla-explicit
   trajectory MPS sampler. Read `qec_twin/forward/scalable/{mps_forward,sv_sampler}` FIRST
   (the reuse target — it is ALREADY the TJM single-site-slice class per 2501.17913); the
   real 17-qutrit circuit is in `xzzx_parser` (ancilla info is there — S10 compiled it
   out, the rebuild reads it back in). Certify {det,obs} records vs the exact QutritDM
   referee (the same 1e-15 oracle that E1-exonerated the old engine). Anti-toy guards
   from the survey: the joint-generator no-split rule (jaschke Appendix A) and the
   purity ≠ trajectory-average arm-consistency check.
5. **RUNG-B**: d5/d7 2D pure-state PEPS + boundary sampling (Rudolph–Tindall engine); run
   the ε_l loop-correlation risk check FIRST; register the bond-saturation bet.
6. **RUNG-C**: coupled/correlated records (the mainline payload; Kam 2603.05474
   process-comb construction for the correlated-noise trajectory distribution).

**Standing constraints (unchanged):** GPU-only model compute, GPU serial (user's live
desktop, no concurrent jobs); scripted-execution discipline; un-led review + theory-fix
BEFORE every load-bearing conclusion; anti-toy independent-GT; src/tests commits need
explicit user confirmation (docs flow normally). Agent spend limit was HIT this session —
some steps were orchestrator-inline.
