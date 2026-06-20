# Phase-1 pre-registration — exact-qutrit d3 XZZX leakage teacher (architecture A)

> **Scope / decision brief.** This registers the **theory-first** gate for Phase 1 of the SIM-ONLY
> non-Pauli teacher–learner program (architecture **A**, user-confirmed 2026-06-20): the **learner is a
> recovered non-Pauli noise model**, the **decoder is the scoring harness**, the **Pauli DEM is the
> baseline/foil**. Phase 1 builds an **exact qutrit (3-level) teacher** for the distance-3 XZZX surface code
> that injects a **known leakage mechanism** (|1⟩→|2⟩ + seepage) and emits labeled `(syndrome-history,
> logical-label)` data.
>
> **Exactness — the d3 engine is a DENSITY MATRIX, and it is genuinely exact (binding correction,
> 2026-06-20, "don't fall to a toy").** At d3 the *data* register is **9 qutrits**: the `3⁹×3⁹ = 5.77 GiB`
> density matrix **fits the 5090** (verified, `outputs/teacher_prereg/exact_floor_feasibility.py`), and
> density-matrix projection equals the full Kraus-branch sum to **1e-16** — so the **R=1 Bayes floor and all
> enumerable observables are computed EXACTLY (no Monte-Carlo, no bias-correction).** This is the qutrit
> analog of the project's exact-backend identity ("real d3 = 2⁹ fits the exact backend"). **Monte-Carlo /
> state-vector / MPS appears ONLY where it is genuinely forced:** (i) **large-R decoder shots** (decoding is
> inherently on sampled shots), and (ii) the **d5/d7 scaling rungs**. The >3× incoherent-surrogate failure
> (2308.08186) is a property of those *approximate scaling tools* and **cannot touch the exact d3 engine.**
>
> Predictions are tagged **(a) exact / (b) prediction-band / (c) heuristic-gate**; undeclared ⇒ (c). House
> style: `docs/whitebox/surface_recover_registration.md`, `docs/.reports/m4_panel/M4A_registration_draft.md`.
> Closes with a metric audit + a rigor audit.

---

## 0. Object & capability — what Phase 1 produces

| Role | Object | Phase-1 status |
|---|---|---|
| **Teacher** | **exact 9-data-qutrit density-matrix** engine for d3 XZZX (extends `forward/exact`), injecting known leakage `(L₁, L₂)` → exact R=1 floor + sampled large-R `(syndrome, logical)` shots | **BUILD** |
| **Learner** | the **recovered non-Pauli noise model** (architecture A) — the twin's RECOVER/UNDERSTAND object | spec only (built Phase ≥4) |
| **Decoder** | the **scoring harness** — a ladder (MWPM → soft-MWPM → TN/neural) + the Bayes floor | rung-0 REUSE; rungs 1–2 later |
| **DEM (Pauli)** | the **baseline/foil** the recovered model must beat; provably cannot represent leakage (2603.18457) | REUSE |

**Isolation contract (binding).** The teacher's channels, `(L₁, L₂)`, and mechanism IDs are
**evaluator-only counterfactual ground truth**. The learner consumes observations only —
`(context, syndrome s, logical m)` — never the teacher's parameters. Scoring is evaluator-side. Mirrors the
existing `mechanisms/` teacher contract.

---

## 1. Geometry & feasibility — `(a)` exact

All numbers cross-verified two independent ways (dataset note ∧ programmatic count from the shipped circuit),
evidence in committed `outputs/teacher_prereg/{feas_d3_qutrit,feas_qubit_index_audit,feas_surplus_qubit_roles,exact_floor_feasibility}.py`.

**1.1 The d3 XZZX code object — `(a)`.** 9 data + 8 measure = **17 informative qubits** (dataset note
`docs/.datasets/google_105Q_surface_code_d3_d5_d7.md` ∧ `metadata.json` agree; 1 logical observable;
distance 3). The shipped *multi-round* `circuit_ideal.stim` declares **20 qubit indices** — 3 surplus inert
(idx 0, 7 = boundary slots reset-but-never-measured; idx 19 = never gated/reset/measured; confirmed absent
from all H/X/Y/CZ/CX/M ops) → droppable. **Note:** at **r01** the circuit is natively **17 qubits / 8
detectors** — the 20-qubit surplus appears only at r10/r13, so the R=1 deliverable (P3) is untouched by it.

**1.2 Source circuit — `(a)`.** `stim 1.16` has **no XZZX generator** (CSS only). The XZZX d3 circuit is
**parsed from the shipped `d3_at_q*/.../circuit_ideal.stim`**. Gate set: `H/X/Y` (1q), **`CZ`** (data↔ancilla
entangler), `R`/`M`, **plus 18 sweep-conditioned `CX`** (`CX sweep[k] q` — classically-controlled data-init
resolving to X-or-I per sweep bit, *not* a 2q entangler; benign on the subspace lift, but **the parser must
handle sweep targets**). All gates have direct 3-level embeddings on `{|0⟩,|1⟩}`. In the exact engine the
data↔ancilla CZ + ancilla measurement is **compiled to a direct stabilizer parity projection on the data
density matrix** (the existing `forward/exact` technique — no ancilla instantiated in the state). Rounds
r01/r10/r13 = 1/10/13 (15 levels up to r250); round-agnostic.

**1.3 Representation: exact 9-data-qutrit DENSITY MATRIX — `(a)`.** The d3 engine evolves the **9 data
qutrits as a `3⁹×3⁹` density matrix** under single-qutrit leakage channels, with each stabilizer measured by
**parity projection** (ancilla measured+reset ⇒ not persistent in the state). Density-matrix evolution **is
the exact integral over all Kraus branches** (verified: `Tr[Πₛρ]` == branch sum to 1e-16) — so the emitted
distribution is **exact**, not estimated. A qutrit *17-qubit* density matrix (3¹⁷×3¹⁷ ≈ 0.2 EB) is infeasible
— which is *why* the 17-qubit / state-vector path is the **scaling** tool, not the d3 engine.

**1.4 Memory feasibility — `(a)`.**

| object | dim | bytes c128 | verdict on 32 GB |
|---|---|---|---|
| **9-data-qutrit density matrix (the d3 EXACT engine)** | 3⁹×3⁹ | **5.77 GiB** | **FITS — 5.5× headroom** |
| 17-qutrit state vector (scaling/MC tool, d5/d7 prep) | 3¹⁷ | 1.92 GiB | fits, but MC-only (Kraus-sampled) |
| 17-qutrit density matrix (exact 17q) | 3¹⁷×3¹⁷ | 0.2 EB | infeasible — forces sampling at 17q |

⇒ **exact d3 = the 5.77 GiB data density matrix.** (Static counts; no run.)

**1.5 Backend — `(a)`.** `forward/exact` is **qubit-only** density matrix (`2ⁿ×2ⁿ`, ≤~15q) but already ships
the **parity-projection primitives** (`project_parity`, `measure_parity_enumerate`, `apply_channel_local`,
`apply_kraus` — confirmed present). The d3 engine **EXTENDS these from 2ⁿ to 3ⁿ** (qutrit density matrix on 9
data) — **no new algorithm**. Its existing "leakage" (M34) is a 2-level surrogate (not a real `|2⟩`) and is
replaced. The `L₁=L₂=0` limit reduces to the existing **9-data 2⁹ exact qubit path** (full scale, not a
window).

**1.6 Compute — GPU (binding).** Model compute → **GPU** (torch CUDA tensors; density-matrix apply/project =
large contractions, GPU-favorable). **No CPU fallback.** The fused-Kraus kernel is 2-level only; a qutrit
kernel is a deferred optimization — Phase-1 correctness runs on plain torch CUDA ops on the 5.77 GiB matrix.

---

## 2. The injected mechanism — leakage `(L₁, L₂)` (the teacher's known ground truth)

**2.1 Channel — full Wood-Gambetta leakage (coherent + dissipative); `(a)` for the evolution, validated
against an INDEPENDENT oracle.** The qutrit (3×3) leakage channel is the **exact integral of a Lindbladian**
with a **coherent `|1⟩↔|2⟩` exchange** `H = θ(|1⟩⟨2|+|2⟩⟨1|)` (generates leakage **and** the non-Pauli
coherence `C_L>0` — Wood-Gambetta 1704.03081 Eqs.55-59), a **dissipative seepage** jump `|1⟩⟨2|` (rate
`g_seep` → WG `L₂`), and an optional **incoherent heating** jump (rate `g_heat`, `C_L=0`) enabling a
coherent-vs-incoherent **ablation at matched `L₁`**. Parameterized by `(θ, g_seep, g_heat)`; the
**field-standard rates `(L₁, L₂)` and `C_L` are DERIVED and verified** via WG-Eq.2 `L₁=(1/d₁)Tr[Π₂E(Π₁)]`
(**never `L₁+L₂`; the ratio + `C_L` are the diagnostics**; `C_L ≡ ‖P_C(ρ)‖₁`, the trace-norm of the
off-diagonal block — WG Eq.31, **not** the bare `|ρ[1,2]|`). CPTP by construction; **validated TWO ways:**
(i) an INDEPENDENT qutip Lindbladian oracle at the channel level (`E(ρ)` on random states, *not* a Kraus
re-encoding, ≤1e-10), and (ii) — the definitive "is it WG" test — against **Wood-Gambetta's ANALYTIC closed
forms**: the unitary `L_j=sin²(θ)/d_j` + `C_L=|sin 2θ|` (Eqs.58-59), the dissipative `L₁,L₂` (Eqs.71-72), and
**Lemma 2** rate-additivity to `O(dt²)` — all to machine precision (`outputs/teacher_prereg/{wg_leakage_channel_reference,wg_closed_form_validation}.py`).
Applied exactly to the data density matrix. **PHYSICS CORRECTION (2026-06-20, toy audit):** the first build shipped a purely
INCOHERENT channel (`C_L=0`, the WG dissipative branch only) with a rate **2× off** the WG definition; both
were independently confirmed (`outputs/teacher_prereg/audit_verify_leakage_physics.py`) and replaced by this
full coherent+dissipative channel. **"Exact" qualifies the density-matrix EVOLUTION, not a claim that this is
the unique device channel** — it is a faithful, field-standard WG leakage model.

**2.2 Rates — `(c)` design constants (near-threshold siting).** First pass, per-qubit stochastic: `L₁ ∈
[1×10⁻³, 5×10⁻³]/cycle` (Miao 2211.04728 ~5×10⁻³/cycle), `L₂ ∈ [5×10⁻², 1×10⁻¹]/cycle` (thermal-like
L₂/L₁ ≈ 20–50; McEwen 2102.06131 γ↑~0.1% / γ↓~8–9%/round, no-reset). **No DQLR removal.** **Leaked-ancilla
readout map — `(c)`, pinned not "random":** a leaked measure qubit is assigned a **biased outcome** per the
device model. **Only the DIRECTION is grounded** (`|2⟩` sits above `|1⟩` in the IQ plane ⇒ reads `|1⟩`-like,
so `b = P(|2⟩ reads |1⟩-like) > 0.5` — Wood-Gambetta/Miao); **the MAGNITUDE is NOT pinned** — any single value
(e.g. 0.9) would be an invented toy constant. We therefore **SWEEP `b ∈ [0.5, 1.0]` and report the R=1 floor
as a bracket** `[LER*(b=0.5), LER*(b=1.0)]`, not a point estimate. The `|2⟩` population on a support is
`O(leakage rate) ≈ 5×10⁻³`, so the floor should be **weakly sensitive** to `b` at R=1 (tight bracket ⇒
leaked-readout immaterial at R=1, reported as such); a **wide** bracket is a finding ⇒ ground `b` from the
device `|2⟩` **IQ position via the proper Gaussian-IQ readout POVM** (the Pattison/AlphaQubit soft-readout axis,
Phase-3) — **never an invented number**. (Addresses contradiction-point #6 + the toy-constant challenge.)

**2.3 Coherence is now CARRIED — but invisible at R=1; it is the P4 lever — `(a)`.** The channel injects
`C_L>0` (§2.1) and the density-matrix engine keeps it exactly (`C_L ≤ 2√(L(1−L))`, WG Props.1–2). **But at
R=1 this coherence is INVISIBLE to the syndrome floor:** the readout POVM is diagonal in the measurement
basis, so `P(s)=Tr[Eₛρ]` traces only **populations** — the `|1⟩-|2⟩` coherence does not enter (the
[[project-coherence-not-identifiable-syndrome-only]] result, exact here). Consequences (load-bearing): the
**R=1 floor (P3) depends on populations only** — coherent `θ` vs incoherent `g_heat` at matched `L₁` give the
**same R=1 floor** — and the **coherence headroom appears only at P4 (large R)**, where it evolves across
rounds. The coherent-vs-incoherent **ablation** (§2.1) is the clean measurement of that P4 headroom; a P4 gap
that *vanishes* under the incoherent-`g_heat` arm at matched `L₁` is positive evidence the headroom is genuinely
the coherence (not just population correlation).

**2.4 Deferred physics + the P4 risk it creates (declared).** Coherent leakage **transport** (CZ-mediated
`|21⟩↔|03⟩`, Miao Fig. 2b — requires persistent ancilla state, pushing toward the 17q/scaling regime) and the
measurement-time T₁ asymmetry are **Phase-1b extensions**; first pass = per-qubit stochastic `(L₁, L₂)`.
**Named risk:** transport is plausibly *where the multi-round, multi-qubit correlations live* — the structure
P4 bets a strong decoder exploits. So **a LOW P4 miss is ambiguous between "leakage carries little decodable
headroom" and "the first-pass model is too simple"**; routing: a low P4 miss triggers **adding transport
before** any conclusion (and a NO-GO requires the transport-bearing model).

**2.5 Sampling budget — `(c)`/`(b)`, scoped to P4 LARGE-R decoder shots ONLY.** The exact R=1 floor (P3) is
**enumerated, not sampled** — it carries no sampling budget. Large-R decoder scoring (P4) is on **sampled
shots** (per-round syndrome sampling off the exact data density matrix — exact data state, honestly-sampled
measurement outcomes). For those: **design constant `N = 10⁶` paired shots per `(basis, R, leakage-regime)`**;
rationale `(b)`: at LER ~0.05 the GO-threshold gap (~0.002) is ≳9σ at `N=10⁶` (`SE≈2.2×10⁻⁴`), tighter under
paired McNemar. **A committed power script pins the achieved CI before the gate.**

**2.6 The full-physics (transport) teacher = sign-problem-free QT-MC, certified by a ladder — `(a)`/`(b)`.**
Coherent leakage *transport* couples data+ancilla ⇒ the exact object is the **17-qutrit** state (3¹⁷×3¹⁷ ≈
0.2 EB — **no feasible exact oracle**). The transport-bearing teacher is therefore a **quantum-trajectory
(Kraus/jump) Monte-Carlo** on the 17-qutrit pure state (3¹⁷ = 1.92 GiB/trajectory, sampled). **This MC is
sign-problem-FREE `(a)`:** leakage/seepage/T1/T2/transport are all completely-positive, positive-rate
(Markovian), so jump probabilities `pₘ = ⟨ψ|Kₘ†Kₘ|ψ⟩ ≥ 0` are Born-positive and a pure-state trajectory
carries **no signed walkers** — categorically distinct from signed-walker *density-matrix* QMC (Shen-Lidar
2502.18929), whose sign problem is intrinsic to sampling the **Liouvillian superoperator** in a fixed basis
(and exists even for Markovian dynamics). Because there is **no exact 17-qutrit oracle**, the QT-MC is
certified by a **LADDER, not by "exact":** (a) local limit (transport→0) **bit-matches the exact 9-data DM**;
(b) a **single-plaquette** instance (~4–5 qutrits = 3⁵, trivially exact) certifies the transport physics;
(c) **cross-method** agreement vs the MPS-trajectory (2308.08186) at d3; (d) MC self-convergence `O(1/√N)`.
**Honest status:** the transport teacher is a **certified MC, not exact** — reported as such, never
"machine-exact". **Engine placement (decided this checkpoint):** Phase-1 stays strictly **CP/Markovian**
(sign-problem-free QT, exact-DM-certified). **Shen-Lidar 2502.18929 is reserved for a future NON-MARKOVIAN
axis** (correlated/colored/memory noise, negative rates — where QT fails); it is **NOT** the scaling carrier
(its pseudo-sparsity premise collapses exactly where our signal lives — coherent over-rotation + transport add
off-diagonals; near threshold `λ→O(1)`). **Scaling (d5/d7) = the MPS-trajectory route (2308.08186)**, certified
against the d3 exact DM.

---

## 3. The model (learner) + the scoring ladder

**3.1 Learner — architecture A.** the **recovered non-Pauli noise model** (built Phase ≥4 as a TN-affine
GNN/Transformer that recovers the noise structure and decodes with it). Phase 1 produces the data + the floor.

**3.2 Decoder ladder (the scorer).**

| rung | decoder | lever | Phase |
|---|---|---|---|
| 0 | MWPM + Pauli DEM (`pymatching`, frozen G) | edge weights only (= a Pauli DEM) | **rung-0 REUSE now** |
| 1 | soft-MWPM (Pattison 2107.13589) | + soft Gaussian-IQ readout, `w(e)=(2/σ²)|μ|` | Phase 3 |
| 2 | TN-MLD / neural (near-ML) | + correlations + leakage + soft (**strong-decoder proxy for the optimum**) | Phase 4 |
| ∞ | Bayes floor `LER*=½(1−TV)` | **EXACT at R=1** (enumerated); sandwich at large R | Phase 2 |

`%ΔLER` between rungs attributes headroom to `{weights, soft, correlation/leakage}`. **Binding fact:** MWPM's
sufficient statistic *is* a Pauli DEM → `pymatching` is used **only as the floor (rung-0) + soft rung
(rung-1)**, never as the contribution decoder.

---

## 4. Predictions (predict-before-measure; tagged + routed)

**P1 — feasibility `(a)` [PROVEN].** the 9-data-qutrit density matrix (5.77 GiB) fits the 5090 (5.5×
headroom), and density-matrix projection == exact Kraus-branch sum to 1e-16. *Established* by
`outputs/teacher_prereg/exact_floor_feasibility.py`. Routing: if a d3 build needs persistent ancilla (e.g.
full transport) the data-only density matrix no longer suffices → escalate to a windowed/scaling rung,
explicitly.

**P2 — correctness `(a)` [verify in build].** (i) the qutrit leakage Kraus is CPTP to ≤1e-12; (ii) the
`L₁=L₂=0` reduction to the **2⁹ exact qubit path** is verified **bit-for-bit** on the toy all-Z code + the
5-site real sub-register, and the **full n=9 codestate is independently valid** (`⟨Sg⟩=+1` for all 8
stabilizers, `⟨Z_L⟩=±1`, reviewer-checked at 3⁹); the **full-9-data mixed-X/Z distribution** bit-for-bit needs
a mixed-X/Z 2⁹ oracle and is a **follow-up** (stated, NOT overclaimed at full scale — pre-run review O2);
(iii) single-channel application matches **qutip** to ≤1e-10. Routing: any miss ⇒ the teacher is wrong; halt
before emitting data.

**P3 — R=1 EXACT LOCAL SANITY FLOOR `(b)` (scope-limited; NOT a headroom claim).** At **r01** the **exact**
Bayes floor `LER*=½(1−TV(P₀,P₁))` is computed by **256-cell stabilizer-parity enumeration on the 5.77 GiB data
density matrix** (exact `P₀,P₁`, exact TV — no plug-in, no bias-correction). The **floor-vs-Pauli-MWPM gap is
≈0**: band **[−2%, +2%] %ΔLER**, and near-zero is **expected**.
**SCOPE (claims discipline, user 2026-06-20) — binding:** P3's *only* purpose is to **validate the exact backend
+ the local leakage physics**; its *only* conclusion is the **local, single-round, diagonal-readout floor**. It
**does NOT and CANNOT establish full non-Pauli headroom** — that is P4. A near-zero R=1 gap is a **successful
sanity check**, never evidence for *or against* the headroom. Any report of P3 must carry this scope; the
headline never reads "the d3 non-Pauli floor."

**P4 — R>1 DECODER-HEADROOM TEST `(b)` (the REAL non-Pauli test — THIS is the headline, not P3).** The genuine
non-Pauli headroom lives at **multi-round `R ∈ {3, 5, 10}` (or more)** and **requires the richer physics P3
deliberately lacks** — a P4 run is only valid if it includes: **(1) leakage persistence + seepage** (the leaked
`|2⟩` population carrying across rounds with `L₂` as its lifetime — temporal memory), **(2) transport /
ancilla-mediated effects** (CZ-mediated leakage spread — needs the persistent-ancilla regime, §2.4 Phase-1b),
and **(3) soft readout** if available (Pattison IQ, Phase-3). Because the Bayes-floor lower bound is **vacuous
at `R≳3`** (ledger), the operative metric is the **gap across a three-rung decoder comparison** on sampled
shots, `%ΔLER` = reduction (positive = better):

> **(0) Pauli-DEM / MWPM floor  →  (2) leakage-aware learner / TN / neural / richer inference  →  (∞) Bayes or a strong-diagnostic ceiling**

| R | central `%ΔLER` (strong vs Pauli) | band | meaning |
|---|---|---|---|
| 1 | <1% | [−2%, +2%] | invisible single-round (= **P3 sanity floor**, not headroom) |
| 3 | ~4% | [1%, 8%] | persistence onset (first genuine multi-round signal) |
| 5 | 8% | [4%, 12%] | multi-round leakage correlations exploitable |
| 10 | 10% | [5%, 15%] | accumulated-tail plateau |

**Calibration honesty:** a **best-estimate band, not "conservative."** Pattison's +25%→~10–17% bounds the
**soft (rung-1) lever**, not the **leakage-correlation (rung-2) lever** — a loose analogy. The win is
**correlation structure** the Pauli DEM cannot represent **regardless of marginal-weight tuning** (a
leakage-tuned Pauli baseline would, per 2308.08186, *over*-predict marginal error, so the gap is structural,
not magnitude). **Risk (§2.4):** P4 is **not runnable on the current data-only-DM engine** — it needs the
multi-round + persistent-ancilla/transport build (Phase-1b) and the decoder rungs; a P4 run that omits transport
under-tests the headroom, and a low result there is **ambiguous** (weak signal vs impoverished model), routing
to Phase-1b not a conclusion.

**P4-ablation — the SEPARATED effect ladder `(b)` (binding; never conflate the rungs).** The headroom must be
**attributed**, not just observed, by isolating each effect:

| rung | mechanism | knob | isolates |
|---|---|---|---|
| R=1 local leakage | **population only** | `θ` (or `g_heat`), 1 round | the diagonal-readout floor (= P3 sanity) |
| R>1 **incoherent** leakage | + **lifetime / temporal-memory** | `g_heat` (`C_L=0`), R rounds | the *classical persistence* contribution |
| R>1 **coherent WG** leakage | + **coherence + transport + temporal-memory** | `θ` (`C_L>0`), R rounds | the *full* non-Pauli signal |
| R>1 **DLM projection** | **same `(L₁,L₂)`, `C_L=0`** (WG Eq.44/62 projection of the coherent channel) | matched `L₁/L₂`, R rounds | the **pure coherence contribution** (= coherent − DLM at matched rates) |

The **coherent − DLM-projection at matched `(L₁,L₂)`** difference is the clean coherence isolator (not an
independently-tuned `g_heat` arm, whose rates would differ); the **incoherent-`g_heat` vs coherent** difference
separates classical persistence from coherence at the channel level.

**P5 — go/no-go gate `(c)`.** **GO** if `%ΔLER ≥ 4%` at R∈{5,7,10} in **≥2** leakage regimes (`L₁=1e-3` and
`5e-3`). **NO-GO** if `%ΔLER ≤ 1%` across R≥5 **with transport included** (per §2.4). **UNDECIDED** (extend to
R=15–20) in between.

**P6 — positive/null controls `(c)`.** (i) **null**: `L₁=0` ⇒ `%ΔLER → 0`; (ii) a **broken-check positive
control must fail loudly**. Routing: a null-control gap ⇒ harness contaminated → halt.

**Declared contradiction-points for the reviewer** (check independently): (1) the 3 surplus qubits are *not*
inert; (2) the gate set does *not* embed faithfully in 3-level (a gate acts on `|2⟩`); (3) the `L₁=L₂=0`
distribution does *not* equal the 2⁹ qubit path bit-for-bit; (4) the R=1 floor gap is *large* (not ≈0); (5)
the large-R gap is an artifact of a *weak* (un-tuned `p_ij`) Pauli baseline, not genuine leakage headroom; (6)
the leaked-ancilla readout map mis-counts detection events; (7) data-only density matrix silently drops
correlations that a real persistent-ancilla process would carry (the transport risk, §2.4).

---

## 5. Build plan (REUSE / EXTEND / BUILD) — M3-scale (≥3 agents + reviewer)

**EXTEND (the core, not from-scratch):** `forward/exact` parity-projection primitives (`project_parity`,
`measure_parity_enumerate`, `apply_channel_local`) from **2ⁿ → 3ⁿ** qutrit density matrices (the exact d3
engine); `mechanisms/catalog.py` (register the leakage mechanism); `contexts/` (probes coupling
computational↔`|2⟩`); `audit/gating.py` (`L₁`↔`L₂` alias check).

**BUILD (new):** the **3×3 leakage/seepage Kraus** `leakage_kraus(L1, L2)` (template
`amplitude_damping_kraus`); the **qutrit leakage teacher** factory mirroring the `mechanisms/` contract; the
**XZZX-circuit parser** → data-density-matrix schedule (incl. sweep-`CX` + leaked-readout map); the **exact
R=1 floor harness** (256-cell parity enumeration → exact TV); the **large-R shot sampler** (per-round syndrome
sampling off the exact density matrix) + its **power script**.

**REUSE:** `decoder/` frozen-MWPM (= rung-0); `knobs/` (`do()`+ΔLER); `audit/bands`, `audit/validity`; `qutip`
(channel oracle); the 9-data 2⁹ qubit exact path (the `L₁=L₂=0` oracle, full scale). Declare any MWPM-baseline
dependency. The **count-based floor estimator** (`outputs/phase0_floor_controls.py`) is **only** for sampled
cross-checks — the primary R=1 floor is the exact enumeration, not the bias-corrected plug-in.

**DEFER (per §2.6 engine placement):** (i) the **17-qutrit sign-problem-free QT-MC** = the d3 *transport-bearing*
full-physics teacher (Phase-1b; certified by the §2.6 ladder — no exact 17q oracle); (ii) the **MPS-trajectory**
route (2308.08186) = the **d5/d7 scaling carrier**, certified against the d3 exact DM; (iii) **Shen-Lidar
walker-QMC (2502.18929)** = reserved for a future **non-Markovian** axis ONLY (NOT scaling — pseudo-sparsity
fails where our signal lives).

**Sequencing.** Phase 1 = extend the exact engine + P2 correctness + the **exact R=1 floor** (P3). Phase 2 =
the P4/P5 large-R de-risk (sampled), transport (Phase-1b) added before any NO-GO. Phases 3–4 = soft readout +
learner/decoder. Build runs as ≥3 disjoint-ownership agents (engine-extension / channel+teacher /
parser+floor-harness) + a separate reviewer, after this pre-registration is approved.

---

## 6. Metric audit + rigor audit (house close)

**Metric audit — every score field-standard or flagged (METRICS.md forced ladder).**

| metric | convention | rung |
|---|---|---|
| per-round LER | frozen decoder, exact over enumerated joint (Fowler 1208.0928) | **1** |
| `%ΔLER` | **reduction `(LER_base−LER_new)/LER_base`, positive = better** (matches `reest-dem +2.96%`); raw ledger `ΔLER=LER(do)−LER(base)`, negative=better (Sivak 2406.02700) | **1** |
| TV(P₀,P₁) | `½‖P₀−P₁‖₁ ∈[0,1]` (Cover-Thomas; Nielsen & Chuang §9) | **1** |
| Bayes floor `LER*=½(1−TV)` | **already ledgered** (METRICS.md:268): **EXACT at R=1** (here: exact `P₀,P₁` from the data density matrix — *not* a plug-in); large-R = sandwich, lower bound vacuous at R≳3 ⇒ score = gap-to-optimum vs a named decoder (Nielsen 1401.4788; BSV 1405.4883; DKLP) | **2** |
| coherence cap `C_L≤2√(L(1−L))` | leaked-coherence bound (Wood-Gambetta Props. 1–2) | **2** |
| MRG | bracket width; go/no-go only | **3 ⚠ (c)** |

No new ledger rows required. All Phase-1 scores rung-1/2 field-standard; the only rung-3 item (MRG) is a `(c)`
gate, and it applies **only** to the sampled large-R sandwich — **not** to the exact R=1 floor.

**Rigor audit — every conclusion classified.**
- **`(a)` exact (the ONLY premises):** the 17-vs-20 qubit fact; the 5.77 GiB feasibility + density-matrix==
  branch-sum identity (P1); the qutrit-Kraus CPTP + `{0,1}`-restriction = 2-level identity + the full-scale
  `L₁=L₂=0` distribution identity (P2); **the exact R=1 floor itself (enumerated exact `P₀,P₁`)**.
- **`(b)` registered bets / finite-sample (a miss is a finding, never citable as fact):** the R=1 floor-vs-Pauli
  *gap* (P3 — exact floor, but its value is a registered prediction); the large-R decoder gap on sampled shots
  (P4, with §2.5 CIs).
- **`(c)` gates/controls:** GO/NO-GO (P5); null/positive controls (P6); leakage rates + readout map (§2.2); the
  large-R shot budget (§2.5); MRG.

**No `(b)`/`(c)` item is used as a premise.** The d3 distribution is **exact** (density matrix); sampling
enters only for large-R decoder shots and the d5/d7 scaling rungs, both explicitly flagged.

---

*Review history: independently reviewed (un-led, 2026-06-20) → NEEDS-CHANGES. User checkpoint ("don't fall to
a toy") → the central reviewer fix (#1, "exact→MC-estimated") was **rejected** and the d3 engine corrected to
an **exact 9-data-qutrit density matrix** (verified `exact_floor_feasibility.py`: 5.77 GiB, density==branch-sum
to 1e-16); fixes #2/#4/#5 scoped/revised accordingly (sampling budget → large-R only; exact TV not the
count-plug-in; full-scale 2⁹ oracle not a 6q window); fixes #3/#6/#7/#8/#9 (sweep-CX, transport risk, r01-17q,
leaked-readout map, P4 best-estimate) kept.*
