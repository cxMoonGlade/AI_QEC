# d5/d7 2D Density-Matrix PEPO Carrier — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION **v2**, 2026-07-09. Predictions written BEFORE the engine build and BEFORE
any rung-1/2 run; a miss is a finding, not a re-fit. v2 = the post-un-led-review revision (4
independent reviewers, 2 BLOCKERs + 9 MAJORs folded in — see the REVIEW OUTCOMES appendix; v1 is in
git history). Companion design: `2d_peps_leakage_forward_DESIGN.md` (the ✅ FEASIBILITY OUTCOMES
header + the 2026-06-24 superseding correction are binding; the pure-state §3 body is superseded).
Resume brief: `HANDOFF_pepo_d5d7_resume_2026-07-09.md`.

**Object.** A qutrit (phys leg d²=9 vectorized, complex128, GPU) **2D density-matrix PEPO forward
simulator** for the rotated XZZX d×d surface-code patch (d3 → d5 → d7), producing the syndrome +
leakage record via single-layer Tr(ρΠ) boundary-MPS contraction and Born sampling. Two owned physics
axes ride on it: (i) per-round-INDEPENDENT non-Pauli qutrit leakage (LRU-const), (ii) notion-2
classical multi-time record memory via a per-round-varying data Pauli channel driven by an external
classical latent. This is SIMULATOR infrastructure (mainline per `project-simulator-p0p4-plan-framing`):
correct + fast + oracle-bounded expression; the DEM/decoder/LER are downstream products, never part of
the validity chain. **Scope declaration (S10, binding):** the simulated object is the DATA-REGISTER
COMPILED record law (stabilizer readout as direct Lüders parity channels on the data qutrits — the
same object the d3 gates, the 1D engine, and the exact oracle define); the ancilla-explicit circuit
(ancilla leakage, readout error) is a registered, trigger-gated extension axis, not silently absorbed.

**Symbol definitions (used throughout — v2 fix; the three bonds are DIFFERENT quantities):**
- **D_ρ** — the PEPO **per-bond** operator bond dimension (one virtual leg).
- **K_cut(d, R)** — the **global** operator-Schmidt rank of the evolved ρ across a straight bisection
  of the d×d patch at round R; K_gap = the rank at the spectral-gap cut. (K_cut ≤ ∏_cut D_ρ.)
- **χ_b** — the boundary-MPS bond dimension used to contract Tr(ρΠ) (a TRUNCATED, algorithmic
  quantity; χ_b ≤ K_cut always, and the route's real bet is χ_b ≪ K_cut).

**Why 2D / why density-matrix (settled, evidence on file — v2 honesty fix on the scaling framing).**
The 1D-MPS bond exponent → 2.0 with d for every ordering (`outputs/teacher_prereg/
p11_codestate_ordering.py`): d5 χ≥512–1024 heavy-but-feasible, d7 = 2^14 ≈ 630 GB dead. A pure-state
2D PEPS re-incurs the wall in the contraction (no canonical form ⇒ ⟨ψ|Π|ψ⟩ is a doubled-layer norm,
χ_b ~ D^(2d)). The density-matrix PEPO's Tr(ρΠ) is SINGLE-layer. **Honest exact-rank accounting:**
the exact bisection operator rank of the codestate is 4^(d−1) (§3 P2) — the SAME exponent family as
the 1D wall 4^d; the exact-rank relief is a constant factor only. The PEPO route's actual levers are
(i) the measured SATURATION of K_gap with R (the d3 R-gate: multi-round noise does not grow the gap
rank), (ii) **truncated χ_b ≪ K_cut** in practice (Darmawan–Poulin contract 153 qubits at χ_b = 8),
and (iii) a small per-bond D_ρ. Whether these levers survive at d5 is exactly what rung 2 measures
under the §7 anti-vacuity protocol — the "χ_b ~ 2^d" phrase of earlier docs is a pure-state-PEPS
heuristic and is NOT registered here. The surviving delta (prior-art adjudicated 3-0):
{full-2D} ∩ {explicit qutrit |2⟩ leakage} ∩ {multi-round Born-sampled syndrome} ∩ {dual-bond
(D_ρ, χ_b) truncation certified vs an exact DM oracle} — infrastructure + a narrow real delta.

---

## 0. Grounding ledger (the corresponding papers — all 精读 + noted, unless marked)

| sub-axis / mechanism | mechanism paper | observable / method paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| DM-PEPO carrier, single-layer Tr(ρΠ) | arXiv:1607.06460 (Darmawan–Poulin; **153 data qubits = the 9×17 AD lattice, EXACT contraction**; approximate boundary-MPS χ_b=8 reproduces the exact logical-channel data against an exact column ceiling of 4^W — the truncated-χ_b ≪ K_cut evidence P8 cites; single-round) *(foundational, pre-2022)* | same (syndrome Born probs via sequential conditional check sampling) | `darmawan_poulin_realistic_noise_1607.06460.md` (upgraded 2026-07-09: full-text re-精读, CARRIER ARCHITECTURE FACTS section) | — (new build) |
| Multi-round + leakage TN reference (thin-strip; the wall datum) | arXiv:2308.08186 (Manabe–Suzuki–Darmawan; qutrit MCWF-MPS, 3×d only; GTA overestimates LER >3×) | bond-vs-round saturation; LER | `manabe_suzuki_darmawan_leakage_tn_2308.08186.md` | 1D engine `qec_twin/forward/scalable/mps_forward.py` (stays valid for d3 + thin strip) |
| Truncation DEFAULT: NTU | arXiv:2107.06635 (Dziarmaga; exact NN-cluster metric, Hermitian non-negative, O(D⁸) parallel, ξ~20; demonstrated on d²-leg thermal iPEPO; **caveat: ξ is NOT the sole difficulty factor** — their own hx=2.5/2.9 comparison) *(foundational)* | truncation-error measure Eq. 2; convergence-in-D | `dziarmaga_ntu_truncation_2107.06635.md` | — |
| Truncation escalation: GTU | arXiv:2205.11067 (Dziarmaga; SVDU→NTU→GTU pipeline, +20–30% past NTU) | overlap-per-site O (Eq. 9) as truncation-quality monitor | `dziarmaga_gtu_truncation_2205.11067.md` | — |
| Truncation escalation: Loop update | arXiv:1906.04085 (Zheng–Yang; 4-site plaquette FET) *(foundational)* | cycle entropy on the loop | `zheng_yang_loop_update_1906.04085.md` | — |
| Mixed-state gold standard: FET/WTG | arXiv:2012.12233 (Mc Keever–Szymańska; mixed-state fidelity Eq. 9 truncation; ~10× over SU) *(foundational)* | S_cycle diagnostic (Eq. E1); infidelity I(t) | `mc_keever_stable_ipepo_fet_wtg_2012.12233.md` | — |
| STABILITY failure modes (the engine gates) | arXiv:2012.03095 (Kilda et al.; SU-iPEPO unstable near dissipative criticality; higher D can DESTABILIZE — D=3,4 pass / D=5,6 fail; D=12 passes / D=14 fails; strong dissipation stabilizes, κ≥5.2) *(foundational)* | ε_Λ convergence diagnostic (Eq. 3) — **adapted to our transient in §6.4, not transplanted** | `kilda_ipepo_stability_2012.03095.md` | — |
| Boundary-MPS contraction + Born sampling + GPU | arXiv:2507.11424 (Rudolph–Tindall; one-site variational MPS-MPO fitting; reverse-pass norm cache; >35× GPU) | p(x)/q(x) ratio + sample-KLD quality metrics; per-gate discarded weight | `rudolph_tindall_gpu_peps_2507.11424.md` | — (blueprint only; their code is Julia, fp32 — does not transfer as-is, §5 S8) |
| Positivity-safe structural escalation (LPDO) | arXiv:1412.5746 (Werner et al., locally purified ρ=XX†) *(foundational)* | — | `werner_positive_tensor_network_open_systems_1412.5746.md` | — (registered §5 S9 escalation only) |
| Leakage mechanism (LRU-const) | WG qutrit model (in-repo, QuTiP-derived, oracle-certified); hardware anchor: arXiv:2211.04728 (Miao et al., leakage≈Pauli-after-removal bound) + arXiv:2408.13687 (Willow DQLR deployment; the 105Q count is corroborated via the Rudolph–Tindall note + handoff, not the Willow note itself) | leakage/seepage populations; detector marginals | inventory in memory `project-leakage-lru-const-memory-notion2shadow` | `error_coupling_simulator/mechanisms/qutrit_teachers.py` (`calibrate_theta_for_wg_l1`), `qec_twin/forward/scalable/sv_sampler.py` (`build_within_cycle_leak`/`marshal_within_cycle`) |
| Memory mechanism (notion-2 record memory) | external classical latent z_t → Θ fan-out → per-round data Pauli channel (own construction; CP-div hierarchy per `project-cpdiv-notion-hierarchy-passive-record`) | CMI/G² Anderson–Goodman order test on the **RAW record M_t** (validated instrument: `outputs/twin_validation/corrected_multitime_observable_run.py`, PASS — detector layer OUT of the validity chain) | memories `project-leakage-lru-const-memory-notion2shadow`, `project-simulator-p0p4-plan-framing` | latent source seams in `error_coupling_simulator/source/`; per-round Kraus via the same seam as leak |
| d3 feasibility evidence (the three gates) | own committed exact-DM measurements (§1) | operator-Schmidt χ(ε); sequential-null detector marginals; connected-correlator ξ | `outputs/nonpauli_teacher/pepo_*_d3{_result.json,.log}`; ξ adjudication recorded in DESIGN header + handoff §3 | oracle: `error_coupling_simulator/carrier/exact/qutrit_dm.py` |

Pre-2022 anchors are tagged *(foundational)* per the citation-recency policy: each is the defining
paper of its method with no newer replacement; the 2022–2026 survey
(`outputs/papers/pepo_survey/PEPO_COMPREHENSIVE_MAP.md`, 20 papers) confirms no successor supersedes
them and that NTU remains the 2023–2024-validated workhorse.

---

## 1. The verified d3 base (facts this prereg builds FROM — per-row epistemic class; v2 fix)

All on the exact d3 qutrit density matrix (3⁹×3⁹), p1c physical cell (WG_L1=5e-3, θ=0.102444,
g_seep=0.09, b=0.9, arm A; g_heat=0 per the handoff §3 — not recorded in the JSON cell dicts),
non-selective sequential Lüders measurement on the DATA-REGISTER COMPILED circuit (S10 — all rows
below carry that scope), straight cut A=[0,1,2] | B=[3..8] (boundary = d = 3). Scripts
un-led-reviewed before every GPU run (5-for-5 on silent-wrong-answer blockers).

| Fact | Value | Class | Source |
|---|---|---|---|
| Operator-Schmidt bond χ(1e-6) across the cut, R=1..10 | **16, FLAT** (= codestate operator rank: n_cross=2 canonical crossing pairs → (2²)²) | (a) exact spectrum of the exact DM | `pepo_feasibility_drho_vs_round_d3_result.json` (SATURATE_FEASIBLE) |
| Purity decay (mechanism live) | 0.9907 → 0.9150 monotone over R=1..10 | (a) | same |
| χ(1e-8) (tail) | ≈50–53 (gap block + ~35 tail components; DESIGN wording "≤1e-7 weight each") | **(b) proxy** — from the eps-map TRUNCATED-propagation arm (`pepo_record_error_vs_eps_d3_result.json`, 1e-08 arm `chi_by_round`). ⚠ the drho JSON's own `chi_1e8` column (204–729) is the float32-corrupted v1 artifact, superseded, internally impossible (729 > rank_full=566) — DO NOT USE | record JSON |
| Record error at gap-cut, ε*∈{1e-3,1e-4,1e-6} (all cut at the SAME χ=16) | max dp = 6.65e-6 @R=10; **worst dp/bar = 0.0167 (60× margin)** at N=1e6, z=4 | (a) as arithmetic on exact-vs-truncated marginals; its role as an ENGINE bound is (b) (S1: optimistic single-cut proxy) | `pepo_record_error_vs_eps_d3_result.json` (RECORD_FEASIBLE) |
| dp_max(R) growth shape | **SUPER-linear: per-round increments rise 2.4e-7 → 1.17e-6 over R=2..10 (fitted exponent ≈1.9–2.1)**; trace_shift ≈ linear | (a) arithmetic on the ledger | same, `dp_max_by_round` (v2 fix — v1 said "linear", wrong) |
| Deep-cut comparison (ε=1e-8, χ≈50–53) | worst dp/bar = 0.039 — keeps more weight, errs 2.3× MORE (the gap-cut FINDING) | (a) arithmetic; the mechanism reading ("round-stable subspace") is (b) | same |
| Truncation ledger at gap-cut | discarded ≤ 2.5e-7/round; trace_shift ≤ 2.6e-6 @ R=10 | (a) | same, `diag` |
| Dynamical correlation length (fitted sectors) | ξ(Zq)=0.48; ξ(n2)=0.17–0.39 over rounds (max 0.39 @R=2, min 0.17 @R=5, 0.18 @R=10) | **(b) coarse fits** (4–5 distinct distances per sector; the JSON's own scope note flags the coarseness) | `pepo_xi_correlation_length_d3_result.json` |
| X-sector | **NOT FITTED at d3** (raw verdict "NO_FIT": only 2 pairs / 1 distance available — a fit is structurally impossible). Adjudication (recorded in the DESIGN header + handoff §3, PROVISIONAL): the constant signal is the two weight-2 X boundary stabilizers s1=X₀X₂, s6=X₆X₈ — their EXISTENCE is (a)-countable; "⟨XX⟩≈0.99, all other pairs <1e-4" is (b) measured (⟨XX⟩=1 exactly only for the noiseless codestate) | mixed (a)/(b); verdict override is PROVISIONAL, not (a) | same + DESIGN + handoff (v2 fix: v1 mislabeled this "(a)-exact") |
| Classical latent bond cost | **χ(mix)=χ(lo)=χ(hi)=16 every round — BOND-FREE**; X2a mixture identity ~2e-16 | χ equalities (a) as measured integers at d3; the d5 generalization is P5 (b) | same (X2b/X2a) |

**Consequences carried (with honest class):** NTU margin — the FITTED sectors give ξ ≤ 0.5 vs NTU's
demonstrated ξ~20 (a ~40× ratio), **(b)-class and fitted-sector-qualified**; the X-sector dynamical ξ
is unmeasured at d3 (P4 registers its first real measurement at d5, where ≥2 X-distances exist). The
truncation-default choice (NTU) is gated on this (b) evidence plus the §6.4/§6.5 runtime diagnostics —
never on ξ alone.

**Scope caveat (binding):** these are d3-exact-DM facts on the compiled circuit. Any d-scaling
statement below is a REGISTERED PREDICTION ((b)-class), not a fact; rung 2 adjudicates under the §7
anti-vacuity protocol.

---

## 2. The mechanisms (anchored; reuse — nothing re-derived)

1. **Leakage (per-round-independent, LRU-const).** The WG qutrit cell above, applied per CZ layer
   (T4 structural timing, reused declaration), reset each cycle (hardware LRU/DQLR justification:
   Miao 2211.04728, Willow 2408.13687). On the PEPO: a **1-site CPTP qutrit channel on the vectorized
   d²=9 physical leg** — verified at d3 to NOT grow the operator bond (§1 row 1). REUSE:
   `qutrit_teachers.calibrate_theta_for_wg_l1` + the `sv_sampler` within-cycle marshaling. Swept
   range: the p1c cell is the certified anchor; WG_L1 ∈ {2e-3, 5e-3, 1e-2}, g_seep ∈ {0.05, 0.09,
   0.15} are the registered sweep (never a single frozen point for any claim beyond rung-1
   certification).
2. **Memory (notion-2, latent-driven per-round Pauli).** Shared classical latent z_t (external,
   sampled per shot) → Θ fan-out → per-round data-qubit Pauli channel. On the PEPO the latent is
   **per-sample conditioned: the mixture average lives OUTSIDE the TN** — verified BOND-FREE at d3
   (§1 last row). **Registered latent sweep (v2 fix — the fan-out may not be a frozen design point):**
   ≥2 fan-out geometries (uniform-global vs spatially-decaying Θ) × ≥2 coupling strengths. No
   PEPO+non-Markovian seam is needed: that unsolved seam belongs to the parked quantum-bath
   (notion-3 / Branch-B) line. notion-1/CP-div is NOT syndrome-reachable — only its notion-2 shadow.
3. **Codestate.** |m⟩_L for the rotated XZZX d×d patch built directly as a stabilizer-structure
   PEPS/PEPO (projector formula ∏_g (I+g)/2, each ≤4-site projector a local 2D gate); per-bond state
   dim ≤4 structural (XZZX mixed stabilizers) ⇒ per-bond operator dim d*_bond ≤ 16 hard ceiling;
   **the actual d*_bond is a rung-0 counted deliverable** (feeds the §6.4 D-sweep range).
4. **Within-cycle dynamics + measurement.** Reuse the 1D engine's within-cycle schedule parsing
   (real Google patches) verbatim; measurement = non-selective sequential Lüders channel for the
   record-law arm (the p1c pattern), Born sampling + projection/collapse for the sampling arm —
   both under the S10 compiled-circuit scope.

---

## 2A. Constraint ledger (FAITHFULNESS_PROTOCOL Rule II — invariants + a falsifying test EACH; v2 NEW)

Every test below must be DEMONSTRATED to trip (a deliberately-broken variant fails it) before it
counts — no vacuous checks.

| # | Physical invariant | Falsifying test (and its demonstrated-to-trip variant) |
|---|---|---|
| C1 | trace(ρ) = 1 after every channel + truncation (up to the logged trace_shift ledger) | per-round trace print; trip variant: skip trace-renorm |
| C2 | Hermiticity ρ = ρ† | max-abs asymmetry ≤ 1e-12 post-Hermitize; trip variant: drop Hermitize |
| C3 | **Positivity ρ ⪰ 0 / no negative Born probabilities** (NOT guaranteed by NTU/gap-cut — NTU's Hermitian-non-negative guarantee is about the METRIC, not the state; Hermitize+trace-renorm restores C2 only; the known LPDO carrier-transition trap) | d3: min-eigenvalue of the truncated ρ vs oracle (measurable at 3⁹), registered (b)-band \|λ_min\| ≤ 1e-6 (discarded-weight grade); d5: every Born weight Tr(ρΠ_x) checked, any value < −1e-8 logged, cumulative negative mass > 1e-4 ⇒ **STOP** (§5 S9); trip variant: inject a sign-flipped truncation component and show the witness fires |
| C4 | CPTP of every applied channel (Kraus completeness ∑K†K = I to 1e-12) | assert per channel build; trip variant: drop a Kraus element |
| C5 | Stabilizer symmetry pre-noise: ⟨S_g⟩=+1 ∀g, ⟨Z_L⟩=(−1)^m, \|2⟩-mass=0 | (a) zero-tolerance on the built codestate; trip variant: corrupt one projector |
| C6 | \|2⟩-mass under LRU-const: per-round leakage population consistent with the WG cell values (`qutrit_teachers` reference) | compare vs teacher closed-form per round; trip variant: double θ |
| C7 | X2a mixture-algebra identity (latent conditioning commutes with the channel algebra) | ≤1e-14; trip variant: shuffle latent draw order |
| C8 | Clifford-slice wiring == the stim anchor | `certify/anchors/stim_clifford.py`; trip variant: swap two stabilizer supports (CorruptStab) |
| C9 | Every gate the compiled circuit contains is applied (schedule completeness vs the parsed within-cycle schedule) | schedule hash + op count vs the 1D engine's parse; trip variant: drop one CZ layer |
| C10 | The S10 compilation is the DECLARED deviation from the physical circuit (ancilla qutrits + readout not instantiated) — no test can pass it off as the full circuit | claim-scope guard: any output artifact labels the record "compiled/data-register"; the ancilla-explicit extension is trigger-gated (§5 S10) |

---

## 3. Predicted observables (class (b) bands — falsifiable, registered BEFORE the engine exists)

Statistics that may never headline: 2-point TV for memory (multi-time CMI/G² only); D-sweep-alone
convergence (Kilda: non-monotone); "matches the 1D MPS" (TN-vs-TN); any check not demonstrated to
trip.

- **P1 — K_gap(R, d5) saturates.** Mechanism: the per-round Lüders channel projects onto a
  round-stable subspace anchored on the codestate operator algebra; noise adds only a small tail
  (d3 evidence §1). Bet: at the d5 tile, K_gap is **FLAT over R=1..10** (no growth beyond the ~2-round
  transient), **measured under the §7 anti-vacuity protocol** (headroom + cap-not-binding + growth
  witnesses — v2 fix; an engine-internal rank read without headroom is vacuous). Monotone growth ⇒
  the multi-round-wall FINDING (§7 rung 3 alternative).
- **P2 — the gap rank = the codestate operator rank, 4^(d−1) structural bet.** Derivation: for a
  stabilizer state, S(A) = |A| − log₂|S_A| ((a)-class standard formula; equivalently the CANONICAL
  crossing-pair count of Fattal et al. — **the convention is the canonicalized count, NOT the naive
  crossing-generator count, which can differ by 2× in the exponent**; v2 fix). d3 anchor: canonical
  n_cross = 2, measured rank 16 = 4². Registered structural hypothesis: n_cross(d) = d−1 for the
  rotated XZZX straight bisection ⇒ state Schmidt rank 2^(d−1), **operator gap rank 4^(d−1):
  d5 → 256, d7 → 4096**. Rung-0 deliverable: compute n_cross(5) VIA THE ENTROPY FORMULA on the
  actual d5 layout ((a)-countable) — it REPLACES d−1 if it differs and the bet transfers to
  4^n_cross. Band (TWO-SIDED, v2 fix): measured K_gap(d5) ∈ [4^n_cross / 2, 2·4^n_cross]; above ⇒
  noise lifts the gap (growth finding); below ⇒ the mechanism is misidentified (also a finding).
- **P3 — record faithfulness at d5 (v2: honest superlinear derivation).** The d3 dp_max(R) is
  SUPER-linear (§1: fitted exponent ≈1.9–2.1 — compounding is already present at d3); the registered
  extrapolation therefore uses the MEASURED R=10 endpoint (6.65e-6, which already contains the
  compounding to R=10) scaled by the boundary factor (5/3): predicted worst dp/bar(d5, R≤10) ≈
  0.028. Band with cushion: **worst dp/bar ≤ 0.1 at N=1e6, z=4, R ≤ 10**. HARD SCOPE: R > 10 is
  out-of-band — extending R requires re-registration (superlinear compounding is the registered
  reason; no silent extension). Adjudication instrument = the §7 rung-2 record-evidence bracket
  (window tiles with the G1.8-calibrated embedding bound + convergence invariance + conditional
  two-arm) — NOT a full-patch exact reference, which does not exist at d5 (v2 fix).
- **P4 — dynamical ξ stays ≪ 2 at d5.** Mechanism: ξ is set by the within-round local dynamics +
  per-round measurement decoherence, not by d. Bet: **ξ(d5) ≤ 1.0** on the same connected-correlator
  instrument, PER FITTED SECTOR. **Registered NO_FIT policy (v2 fix — the d3 instrument's known
  failure mode may not be re-adjudicated post hoc):** a NO_FIT sector is acceptable ONLY if the
  constant-correlator signal is positively identified as codestate structure (the (a)-countable
  boundary-stabilizer test: the signal sits exactly on the identified stabilizer pairs and all
  other pairs are below the registered floor); any other NO_FIT ⇒ STOP, no prose adjudication. At
  d5 the X-sector has ≥2 distinct distances ⇒ the X-sector ξ gets its FIRST real fit; it enters the
  same ≤1.0 band. Trip-wire: ξ ≥ 2 in any fitted sector anywhere in the swept cell range ⇒ STOP,
  escalate the ladder (§6.5).
- **P5 — latent stays bond-free at d5:** χ(mix) = χ(arm) at every round (d3: exact equality).
- **P6 — gap-cut ≤ deep-cut record error at d5** (the round-stable-subspace mechanism transfers).
- **P7 — memory display (v2: paired-difference form on the RAW record).** On the validated
  instrument's registered representation (RAW per-stabilizer measurement streams M_t — the detector
  layer stays OUT of the validity chain), with symbolization per §6.7: the latent-driven arm shows a
  CMI/G² memory-order signature STRICTLY EXCEEDING the latent-frozen control arm at matched per-round
  marginals (paired design, same seeds structure). **No absolute "order 0" null is registered** —
  uncorrected data-Pauli parity persistence makes raw records structurally non-order-0 even without
  a latent (the d3 instrument's own documentation); the discriminator is the ARM DIFFERENCE.
- **P8 — χ_b band + the d7 resource rule (v2 NEW — the go/no-go quantity must have a registered
  band).** Bet: the record-faithful boundary-MPS bond at d5 satisfies **χ_b(d5) ∈ [16, 256]**
  (bracket, declared wide: floor = the d3 gap rank; ceiling = the P2 central bet 4^n_cross — NOT
  the P2 band top, which is 512; the D-P χ_b=8
  precedent motivates the low half but is single-round/different noise). The d7 go/no-go does NOT
  gate on P2 alone: it plugs the MEASURED (K_gap, χ_b, D_ρ) at d3+d5 into the registered d7 resource
  formula — boundary-MPS memory ≈ d·χ_b²·d*_bond·16 B per stored boundary + PEPO tensors + the NTU
  O(D⁸) metric workspace + the sampling cache, extrapolated with the measured d3→d5 growth exponent —
  and requires the projected d7 total ≤ **24 GiB** (75% of the 32-GiB card; spark offload only as a
  declared alternative). GO requires P1 ∧ P2 ∧ P3 ∧ the resource projection; any single miss ⇒ NO-GO
  (finding).

---

## 4. Independent ground truth (non-circular; the anti-toy spine)

- **Rung 1 (d3, the certifier):** the exact qutrit DM oracle —
  `error_coupling_simulator/carrier/exact/qutrit_dm.py` (dense density-matrix propagation, NOT a
  tensor network; **hard capacity: 9 qutrits on the 32-GiB card — 3⁹ DM = 5.77 GiB; 3¹⁰ ≈ 52 GiB
  does NOT fit; the "~15q" figure of CLAUDE.md is the QUBIT-era number and does not transfer** —
  v2 fix). Gate: the PEPO engine's {det, obs} joint == the oracle within the MC band (z≤4), zero
  structural tolerance; the sequential-null marginals table of
  `pepo_record_error_vs_eps_d3_result.json` is the frozen reference. Wiring cross-check in the
  Clifford slice via the stim anchor. Scoring routes through the certify seam (`certify/core.py`
  route → controls-first → ledger).
- **Anti-circularity clauses (HARD):** never certify the PEPO against the 1D MPS alone; never
  certify by D-sweep convergence alone (Kilda); never against our own TN-derived expectation; and
  (v2) never adjudicate a rank/growth band on the engine's own truncated spectrum without the §7
  headroom protocol — the instrument that truncates at the gap cannot certify gap flatness unaided.
- **Rung 2 (d5 — no full oracle EXISTS at 25 qutrits; bracketed evidence, PROVISIONAL by
  construction):**
  (i) **9-qutrit embedded-window tile checks** (v2 fix — sized to the real qutrit-DM ceiling):
  compare engine window-marginals on 3×3 data sub-patches vs stand-alone tile oracles under a
  DECLARED boundary treatment; the window-embedding mismatch is itself a bounded simplification
  (S11) whose bound is CALIBRATED AT d3 (gate G1.8: embedded-window-vs-tile mismatch measured where
  both are exact) — the d5 tile check only counts within that calibrated bound;
  (ii) structural exacts: C5 invariants, X2a identity, latent χ-equality;
  (iii) the two-arm cross-check vs the 1D fixed-χ MPS arm (OPT2-3) — **CONDITIONAL: OPT2-3 is an
  unbuilt registered roadmap item (`docs/twin_validation/batched_mps_backend_prereg.md`); if it has
  not landed at rung-2 time, rung 2 proceeds on (i)+(ii) and the verdict records the missing arm
  as a weaker bracket** (v2 fix). Consistency evidence only, never certification.
- **Controls (non-optional, demonstrated-to-trip):** CorruptStab + Shuffle must break the rung-1
  gates; the identical-arms vacuous-PASS guard in every two-arm comparison; every 2A test trips its
  broken variant; every check classified GENUINE vs VACUOUS before any all-pass roll-up.

---

## 5. Bounded simplifications (each declared + bounded; unbounded ⇒ STOP)

| # | Simplification | Class | Bound / control |
|---|---|---|---|
| S1 | D_ρ truncation at the SPECTRAL GAP (not fixed ε) | (c) design rule; ledger (a) | per-cut discarded weight + trace shift printed per round (d3: ≤2.5e-7, ≤2.6e-6 @R10); faithfulness = rung-1 oracle equality; the d3 single-cut measurement is a declared OPTIMISTIC proxy (lower bound on engine error) — the engine gate G1.2 carries its own, larger budget (≤0.1), not the proxy's 0.0167 |
| S2 | Boundary-MPS χ_b truncation (contraction + sampling) | (c) + ledger (a) | discarded-weight ledger; R-sweep convergence of sampled marginals; p(x)/q(x) + sample-KLD diagnostics with importance-sampling correction available; certified at rung 1 vs the oracle |
| S3 | WG qutrit leakage model | declared+bounded in the 1D engine | C_L ≤ 2√(L(1−L)) (Wood–Gambetta); REUSED |
| S4 | Per-CZ-layer leakage injection (Stim structural timing, T4) | (c) | reused declaration; unchanged by the 2D host |
| S5 | LRU-const (per-round-independent) leakage | (b) hardware-anchored | Miao 2211.04728 + Willow DQLR; OPT2-2 (per-round-varying leak) stays PARKED trigger-gated |
| S6 | NTU's finite NN-cluster environment | (b) via measured ξ + runtime diagnostics | fitted-sector ξ ≤ 0.5 at d3 vs NTU's demonstrated ξ~20 (~40× ratio, (b), fitted-sector-qualified; X-sector first fitted at d5 — P4); NTU's own caveat that ξ is not the sole difficulty factor is why escalation is ALSO keyed on the §6.4/S_cycle diagnostics, not ξ alone (v2 fix); ξ≥2 or diagnostic trip ⇒ §6.5 ladder escalation, never silent |
| S7 | Non-selective sequential Lüders channel for the record-law arm | (a) identity at d3 **within the S10 compiled scope** (v2: the shared-blind-spot caveat lives in S10, not here) | same construction the oracle uses; the Born-sampling arm separately gated (G1.1) |
| S8 | float64/complex128 everywhere | (c) hard rule | the float32 `1−ε == 1.0f` trap; no fp32 in any tail/gap/ledger quantity (Rudolph–Tindall's >35× GPU numbers are their Fig.-5 fp32 WALLTIME benchmarks — verified vs the original 2026-07-09; their wavefunction storage quotes are double-precision complex — so the timing numbers do not transfer as-is to a complex128 engine) |
| S9 | **Truncated-ρ positivity is NOT enforced by construction** (v2 NEW — the BLOCKER fix) | (b) banded + (c) STOP rule | Ledger row C3: d3 min-eig band \|λ_min\| ≤ 1e-6 measured vs oracle; d5 runtime negativity witness on every Born weight (< −1e-8 logged; cumulative negative mass > 1e-4 ⇒ STOP); demonstrated-to-trip variant required; REGISTERED ESCALATION: switch the carrier to the locally-purified LPDO form ρ = XX† (Werner 1412.5746 — positivity by construction, at higher bond cost) if the witness trips persistently |
| S10 | **Ancilla-free compilation** (v2 NEW — the BLOCKER fix): no ancilla qutrits instantiated; stabilizer readout compiled to direct data-register Lüders parity channels; hence NO ancilla leakage, NO ancilla-mediated propagation, NO readout error in this build | (b) hardware-anchored scope fence | DECLARED as the build's object definition (header + C10): the simulated record law is the compiled abstraction — the same object the d3 gates, the 1D engine, and the oracle define, so rung-1 certification is INTERNALLY consistent but structurally blind to the compilation itself (shared simplification, stated openly; `phase1_qutrit_leakage_registration.md` §1.2–1.3 documents the technique + its risk list). Within the LRU/DQLR hardware abstraction the residual ancilla-mediated leakage effect is bounded by the Miao leakage≈Pauli-after-removal result ((b)); every output artifact carries the "compiled/data-register" label; the ancilla-explicit circuit (ancilla leakage + readout error) is a REGISTERED TRIGGER-GATED EXTENSION with its own future prereg — no faithfulness claim of this build extends past the compiled scope. ⚠ All §1 d3 feasibility numbers carry this scope; the ancilla-explicit K_gap is a different, unmeasured quantity |
| S11 | **Window-embedding mismatch** of the rung-2 tile checks (v2 NEW): an embedded 3×3 window of the entangled d5 patch ≠ a stand-alone tile | (b) calibrated | G1.8 calibrates the mismatch AT d3 (embedded 2×3/3×2 windows of the d3 patch vs stand-alone tiles — both exactly computable); the d5 tile comparison counts only within the calibrated bound; if the d5 discrepancy exceeds (mismatch bound + truncation budget), the check is INCONCLUSIVE, not failed — declared to avoid confounding truncation error with embedding error |

---

## 6. Engine design decisions (settled defaults + registered gates)

1. **NTU truncation FROM THE START** (Dziarmaga 2107.06635): exact NN-cluster metric, provably
   Hermitian + non-negative (the METRIC — not the state; see S9/C3), O(D⁸) parallel matmul,
   demonstrated on the d²-leg thermal iPEPO. itrSU would suffice at the measured fitted-sector
   ξ ≤ 0.5 but NTU is the margin choice at comparable wall-clock for D ≲ 12.
2. **Truncate at the SPECTRAL GAP, not a fixed ε** (the d3 record-gate FINDING: gap-cut 0.0167 vs
   deep-cut 0.039 — keeping more weight erred 2.3× more).
3. **Classical latent per-sample conditioned OUTSIDE the TN** (X2b: bond-free, exact at d3).
4. **Stability gates — Kilda-DERIVED, adapted to our object (v2 fix: Kilda's ε_Λ is a Vidal-form SU
   steady-state diagnostic; our evolution is a finite-R decohering transient with no NESS and NTU
   has no Λ bond weights — the literal transplant is not evaluable).** Registered adaptations:
   (i) **bond-spectrum stationarity** Δσ(R) = ‖σ̂_R − σ̂_{R−1}‖_∞ on the **ℓ²-NORMALIZED**
   kept STRAIGHT-CUT gap spectra σ̂ = σ/‖σ‖₂ (convention AMENDED v2.3, pre-build, by the rung-1
   contract red-team round 2: the un-normalized convention is refuted by the frozen exact
   dynamics itself — healthy purity decay drifts the raw spectrum ~4.2e-3/round with no plateau,
   so the raw-Δσ gate would fire the Kilda STOP on correct physics; the normalized shape drift
   is ~4e-5. Sorted descending, the shorter spectrum zero-padded when the kept rank changes;
   the per-bond analogue is logged as a diagnostic but the GATE quantity is the straight-cut
   spectrum), logged every round; registered expectation: Δσ plateaus ≤ 1e-3 after the ~2-round
   transient (rounds R ≤ 2 are excluded as gate reads); persistent growth or oscillation of Δσ
   ⇒ the Kilda instability pattern ⇒ STOP.
   (Textual ancestor, verified against the Kilda original 2026-07-09: their own steady-state STOP
   rule is per-bond Λ-spectrum stationarity required for EACH of the four bond matrices Λ[U,D,R,L]
   separately (their App. A.2) — Δσ is the finite-transient analogue of exactly that criterion);
   (ii) per-round discarded weight must plateau (growth with R = the cap-independent growth
   witness, also used by §7);
   (iii) **the D-sweep derived from OUR model (v2 fix — not Kilda's literal 3..6):** sweep
   D ∈ {⌈d*_bond/2⌉, d*_bond, 2·d*_bond, 4·d*_bond} where d*_bond is the rung-0-counted structural
   per-bond operator need (≤16 hard); the monotonicity metric = rung-1 record error + oracle
   distance vs D; a low-D pass that destabilizes at higher D (the Kilda Fig. 6 pattern) ⇒ STOP +
   FET/WTG escalation;
   (iv) independent-oracle certification, NEVER D-sweep alone.
   Regime note ((c)-comfort, not a premise): per-round Lüders ≈ strong dissipation = Kilda's stable
   zone (their κ≥5.2 stabilization), consistent with fitted-sector ξ ≤ 0.5.
5. **Truncation ladder (escalation keyed by ξ AND the runtime diagnostics — v2 fix, ξ is not the
   sole factor per the NTU paper itself):** itrSU (ξ≲2 — tePEPO's own admission) → Loop update
   (1906.04085) → **NTU (ξ~20 demonstrated — Dziarmaga; DEFAULT)** → GTU (2205.11067) → FET/WTG
   (mixed-state gold standard, 2012.12233). ⚠ Provenance note (v2, fact-check finding): the ξ~5
   (Loop) and ξ~30 (GTU) figures circulating in the survey map are REPO-INTERNAL heuristic
   estimates, (c)-class, NOT paper numbers — the paper-anchored points are itrSU ξ≲2 and NTU ξ~20
   only. Escalation triggers: P4 ξ trip, §6.4 Δσ/discarded-weight trip, S_cycle > 1e-3
   ((c)-heuristic from Evenbly via Mc Keever), or a rung-1 gate failing at the max feasible D.
   FET/WTG read-before-build: DONE (精读 on file); S_cycle is logged from rung 1.
6. **Boundary-MPS contraction + Born sampling** per the Rudolph–Tindall blueprint: reverse-pass
   norm cache, forward-pass per-sample conditional sampling, one-site variational MPS-MPO fitting,
   gesvd; sample-quality metrics per S2; adapted to the SINGLE-layer PEPO norm; complex128 (S8).
7. **Multi-stabilizer CMI/G² symbolization (v2 fix — aligned with the validated instrument).** The
   validated d3 instrument operates on the **RAW record M_t** (its own registered config; the
   detector layer is OUT of the validity chain) — the v1 detector-bit-stream default is WITHDRAWN.
   DECISION ((c)-class design constant): default symbolization = **raw per-stabilizer measurement
   streams M_t, single-stabilizer symbols + joint symbols on latent-coupled stabilizer pairs**
   (the pairs Θ actually couples). MANDATORY sensitivity panel over ≥2 alternative symbolizations
   (single-stab only; a non-latent-coupled control pair; a latent-misaligned coarse-graining); the
   latent-frozen control arm runs in every panel cell; the discriminator is the PAIRED ARM
   DIFFERENCE (P7), never an absolute order claim.
8. **Substrate spike (rung 0, (c) engineering decision):** quimb-2D primitives vs self-written
   host. NTU metric + one-site boundary fitting are custom either way. Rung-0 deliverables:
   (i) the substrate decision; (ii) NTU-metric unit test vs dense contraction ((a) zero-tolerance);
   (iii) **n_cross(d5) via the entropy formula** on the actual layout ((a), feeds P2);
   (iv) **d*_bond counted** for the XZZX codestate PEPO ((a), feeds the §6.4 D-sweep).

---

## 7. Validation ladder (gates per rung; no d7 claim until each rung passes)

- **Rung 0 — spike.** The four §6.8 deliverables.
- **Rung 1 — PEPO engine @ d3 == the exact-DM oracle (the certifier).** Gates (crisp bars — v2 fix,
  no "-grade" suffixes):
  G1.1 {det,obs} joint == oracle, MC band z ≤ 4, zero structural tolerance;
  G1.2 sequential-null marginals vs the frozen §1 reference: engine worst dp/bar ≤ **0.1** at
  N=1e6, z=4 (the single-cut 0.0167 is the declared FLOOR reference — the engine, truncating every
  bond every round + the boundary layer, is expected to land in (0.0167, 0.1]; ≤0.1 = pass, the
  P3-derived engine-level budget);
  G1.3 engine gap rank at the d3 straight cut == **16** exactly;
  G1.4 §6.4 diagnostics: Δσ plateau ≤ 1e-3 post-transient, discarded weight plateaus, D-sweep over
  the d*_bond-derived range monotone in oracle distance (Kilda-pattern destabilization ⇒ STOP);
  G1.5 controls trip: CorruptStab, Shuffle, identical-arms guard, and every 2A broken-variant —
  each DEMONSTRATED;
  G1.6 latent bond-free reproduced (χ(mix)=χ(arm));
  G1.7 in-engine ξ re-measurement: ξ(Zq) ∈ [0.2, 0.8], ξ(n2) ∈ [0.1, 0.5] (the §1 d3 values ±
  fit-grade tolerance); NO_FIT handled per the P4 registered policy only;
  G1.8 **window-embedding mismatch calibration** (v2 NEW): embedded 2×3/3×2 windows of the d3 patch
  vs stand-alone tiles, both exact — the measured mismatch becomes the S11 bound for rung 2;
  G1.9 **positivity** (v2 NEW): min-eig of truncated ρ vs oracle within the C3 band; negativity
  witness demonstrated to trip on the sign-flip variant.
- **Rung 2 — d5 tile + cross-checks (adjudicates P1–P8; PROVISIONAL by construction).**
  **Anti-vacuity rank protocol (v2 NEW — binding for P1/P2):** the K_gap(d5) measurement must
  (i) run with per-bond cap D ≥ 2·d*_bond so the cut ceiling ∏_cut D ≥ 4× the P2 band top —
  the PASS requires the kept spectrum to SHOW the gap (≥4× ratio) with kept rank < 0.5× the cap
  product (the gap, not the cap, sets the rank);
  (ii) repeat at cap 2× — the measured rank must agree (cap-limited ⇒ INCONCLUSIVE, not pass);
  (iii) track the cap-independent growth witness (per-round discarded weight at fixed cap must not
  grow with R).
  Record faithfulness per P3 via the (i)–(iii) bracket of §4 rung 2 (tiles within the G1.8 bound;
  convergence invariance; two-arm CONDITIONAL on OPT2-3). Memory display per P7.
  **Go/no-go = P8:** P1 ∧ P2 ∧ P3 ∧ the d7 resource projection ≤ 24 GiB ⇒ d7 GO; any miss ⇒ NO-GO.
- **Rung 3 — d7** only on rung-2 GO; else the honest FINDING: "the multi-round full d×d hits its
  own wall → the thin 3×d strip (Manabe's choice) is the feasible path" — a finding, never partial
  success.

---

## 8. Build org + disciplines (contract-first; heavy-task rule)

- **4 disjoint-ownership builders + un-led review** (DESIGN §6 updated to the DM-PEPO architecture):
  A1 codestate-PEPO; A2 dynamics (d²=9-leg channels + NTU); A3 boundary-MPS
  contraction/sampling/collapse; A4 validation (certify wiring + the rung scripts + the 2A ledger
  tests). **OPT2-3 (the 1D fixed-χ d5 arm) has NO owner in this decomposition — it is a separate
  registered build (batched-MPS prereg scope); rung 2's two-arm check is CONDITIONAL on it** (v2
  fix). Long runs orchestrator-driven, never inside a sub-agent.
- **Reviewer protocol:** un-led (stage problem + ultimate goal + artifact ONLY); un-led review
  BEFORE every GPU run (the 5-for-5 record); contract-build pipeline for the src build.
- **Execution:** GPU-only complex128, serial (live desktop); scripted-execution discipline (asserts
  + printed evidence + flush + `__main__` guard), scripts under `outputs/nonpauli_teacher/`; VRAM
  budgeted per script (the 29-GiB near-miss is on record).
- **src placement (PROPOSAL, commit-gated on explicit user confirmation):**
  `error_coupling_simulator/carrier/pepo/`; `qec_twin/forward/scalable/` keeps the 1D arms. No src
  change lands without user confirmation; docs/outputs commit normally.

## 9. Scope fences (non-goals of this build)

- No d7 claim before rung 2; every d-scaling statement stays (b)/PROVISIONAL until measured under
  the §7 protocol; R > 10 record-error claims require re-registration (P3).
- The S10 compiled-circuit scope bounds EVERY faithfulness claim; the ancilla-explicit extension is
  trigger-gated with its own future prereg.
- OPT2-2 (per-round-varying leak) stays PARKED trigger-gated.
- No quantum-bath / notion-3 / pseudomode content; no notion-1 claim from syndrome records.
- DEM / decoder / LER never enter the validity chain; LER is the product.
- No Pauli-twirl anywhere in the leakage path (Manabe: GTA overestimates LER >3×).
- The finance/twin framings stay retired; this is the simulator mainline.

---

## Appendix — RUNG-0 OUTCOMES (2026-07-09, adjudicated; scripts + logs + JSONs under
## `outputs/nonpauli_teacher/pepo_rung0_*`)

All four §6.8 deliverables landed; every run un-led-reviewed BEFORE execution (3
reviewers; 1 BLOCKER + 3 MAJORs caught pre-run: an 11.3-TB open-tensor referee OOM at
d_phys=9, a statevector survival bar sitting INSIDE the 2^-25 signal scale (~74%
spurious-abort odds), the d*_bond ceiling mislabeled as the need, and a missing
logical-no-fallback/symplectic guard — all fixed pre-run).

- **(iii) n_cross — RP1_ALL_HIT, the P2 bet basis is now COUNTED + MEASURED, not
  hypothesized.** On all SIX real Google patches (`xzzx_parser`, never a textbook
  layout): bisection n_cross = d−1 exactly — d3_at_q6_7: 2; d5_at_q4_7/q6_5/q6_9/q8_7:
  4 (all four); d7_at_q6_7: 6. ⇒ K_gap(d5)=256, K_gap(d7)=4096 (codestate operator
  rank; P2's central bet CONFIRMED as registered, band unchanged). Verification
  triangle all-green: V1 brute-force subgroup enumeration (d3, every cut), V2 exact
  GPU statevector Schmidt rank (d3 AND all four d5 patches: rank 16 = 2⁴ measured),
  V3 the frozen §1 anchor (4^n_cross == 16). Guards all-green: G1 symplectic
  commutation (every generator pair, every patch), G2 stim-flow re-verification of the
  logical on the raw circuit (no parser fallback fired), G3 S(A)==S(B) at every cut.
  Structural datum: s_t = 2·n_cross at EVERY straight cut on every patch (each
  independent crossing generator carries one redundant partner).
- **(iv) d*_bond — the §6.4 D-sweep is pinned to D ∈ {2, 4, 8, 16}.** Counted both
  ends of the bracket: perbond_FLOOR = 4^(n_cross/s_t) = 2.000 at every bisection
  (below the ≤4 expectation) and dstar_bond_CEILING = 4^m_max = 16 with m_max = 2 on
  every patch (RP2 HIT). The registered {⌈d*/2⌉, d*, 2d*, 4d*} formula instantiates
  as the floor-to-ceiling sweep {2, 4, 8, 16}.
- **(ii) NTU-metric unit — NTU_METRIC_UNIT_PASS.** Structured Fig.-4 assembly ==
  monolithic dense einsum at ~5e-16 rel (bars 1e-11) at BOTH d_phys=2 and d_phys=9;
  Hermitian ~1e-16; PSD; quadratic form == closed dense norm ~4e-16; pinv step reduces
  ε and matches dense ~2e-16; the parallel-bond mis-wire trip variant fires (3-6e-2).
  **FINDING (the registered check demonstrating its own teeth):** the FIRST run's C4
  caught a metric ROW-CONVENTION bug the un-led review had passed — with rows = the
  KET insertion, ε = v†gv is off by Re(v₁*v₂g₁₂) vs Re(v₁v₂*g₁₂) (measured rel 0.199);
  the metric's rows must be the BRA insertion. The engine seed carries the fixed
  convention (g[(IJ),(ij)] = ⟨cluster(IJ)|cluster(ij)⟩).
- **(i) substrate — DECISION ((c)): quimb-2D as the tensor HOST.** Evidence: quimb
  1.14.0 ships PEPS/PEPO/TensorNetwork2D with `contract_boundary_from*` plumbing (E1);
  a 2×2 PEPS norm contraction PRESERVES torch-cuda-complex128 backing end-to-end (E2
  PASS — no silent numpy cast); the 1D engine coexists against the same quimb (E3).
  The NTU metric + the one-site boundary-MPS fitting remain CUSTOM modules on top
  (as registered — the host provides containers/contraction only).

Consequence: rung 0 is CLOSED; no registered band or gate moved (P2/P8 confirmed as
written). Next = rung 1, the PEPO engine build (§7 gates G1.1–G1.9; /contract-build;
src placement proposal `error_coupling_simulator/carrier/pepo/`, commit-gated).

## Appendix — REVIEW OUTCOMES (v1 → v2, 2026-07-09)

Un-led adversarial review of v1: 3 independent reviewers (identical un-led briefs: problem + goal +
artifact only) + 1 exhaustive fact-checker. Every §1 number and every reuse pointer VERIFIED against
the committed artifacts (fact-check PASS, zero numeric mismatches). Findings folded into v2:

- **BLOCKER (R1/R3): truncated-ρ positivity undeclared/unmonitored** (NTU guarantees a non-negative
  METRIC, not state; the LPDO trap) → 2A ledger row C3 + S9 (d3 min-eig band, d5 negativity witness
  + STOP rule, LPDO ρ=XX† registered escalation) + gate G1.9.
- **BLOCKER (R2/R3): the ancilla-free compilation was absent from §5** (shared engine-oracle blind
  spot) → S10 scope declaration (header + C10 + every-artifact labeling + trigger-gated
  ancilla-explicit extension); all d3 evidence explicitly scope-tagged.
- **MAJOR (R1/R2/R3): the rung-2 instrument** — "≤~15q" was the qubit-era figure (qutrit DM caps at
  9 sites); no full d5 oracle exists; engine-internal rank reads were vacuous → §4 rung-2 rewritten
  (9-qutrit tiles + G1.8-calibrated S11 embedding bound), §7 anti-vacuity rank protocol (headroom,
  cap-doubling, cap-independent growth witness).
- **MAJOR (R1/R3): P3's "linear in R" premise contradicted its own JSON** (fitted exponent
  ≈1.9–2.1) → §1 superlinearity row; P3 re-derived from the measured R=10 endpoint; R>10 fenced.
- **MAJOR (R2/R3): χ_b had no registered band; D_ρ conflated per-bond vs global rank; the "2^d
  relief" framing contradicted P2's 4^(d−1)** → symbol block; honest exact-rank accounting in the
  header; P8 χ_b band + d7 resource formula in the go/no-go.
- **MAJOR (R1): §6.7's detector-bit symbolization contradicted the validated instrument (raw M_t);
  the "order 0" null ignored parity persistence** → §6.7 raw-M_t default; P7 paired-difference form.
- **MAJOR (R1/R2/R3 + fact-check): the ξ adjudication** (committed verdict NO_FIT; "(a)-exact"
  overclaim; c_max=0.9988≠1; sector-unqualified "ξ≤0.5") → §1 per-row classes, X-sector row
  rewritten (PROVISIONAL, mixed (a)/(b), cites the DESIGN+handoff adjudication record), P4 NO_FIT
  policy, S6 fitted-sector qualification.
- **MAJOR (R1): G1.4 transplanted Kilda's steady-state ε_Λ + literal D=3..6** → §6.4 Δσ bond-spectrum
  stationarity + discarded-weight plateau + d*_bond-derived D-sweep (d*_bond = rung-0 count).
- **MAJOR→MINOR set:** "-grade" gate bars → crisp numbers (G1.2 ≤0.1 with 0.0167 as floor; G1.7
  intervals); OPT2-3 dependency made CONDITIONAL + ownership noted; n_cross pinned to the canonical
  (entropy-formula) convention with a TWO-SIDED band; χ(1e-8) provenance corrected (record-JSON arm;
  drho column marked corrupt); ξ(n2) reported as range 0.17–0.39; ladder ξ~5/ξ~30 flagged as
  repo-internal heuristics; Loop/GTU/D-P/Willow citation-target fixes; §5→§6.5 cross-ref; latent
  Θ sweep registered.
