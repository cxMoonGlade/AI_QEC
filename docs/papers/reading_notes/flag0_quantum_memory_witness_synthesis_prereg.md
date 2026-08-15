# Synthesis note (精读 of 4 sources → predict-before-measure prereg): Flag-0 closure — "revival ≠ quantum memory," the correct witness to build, and the Flag-#1 active-vs-passive gap

> **Provenance (2026-07-06): SYNTHESIS over four full-text (精读) reading notes.** No new
> paper read here; this note fuses and adjudicates the four acquired notes below into a
> corrected-path pre-registration. Every load-bearing claim is tagged `[paper]` (transcribed
> from one of the four notes, with the arXiv id) vs `[ours]` (project inference). The four
> grounding notes:
> - `phase_diagrams_information_backflow_2601.18822.md` (Nakagawa, full-text) — backflow is kernel-driven, quantum/classical-symmetric.
> - `backer_revealing_quantum_nature_memory_2510.19522.md` (Bäcker/Palaparthy/Strunz, full-text) — applied IBM `C♯<C` assistance witness on the ACTIVE Choi object.
> - `giarmatzi_witnessing_quantum_memory_process_tensor_1811.03722.md` (Giarmatzi–Costa, full-text) — process-tensor quantum-memory witness = temporal entanglement of W, requires ACTIVE interventions.
> - `taranto_hierarchy_multitime_classical_memory_2307.11905.md` (Taranto–Quintino–Murao–Milz, full-text) — strict multi-time hierarchy M ⊊ CDC ⊊ CM ⊊ SEP ⊊ QM, classical memory = EBC feed-forward instruments.
>
> **Adjudication target:** (1) grounded Flag-0 verdict; (2) which tool to build — the E♯<E
> assistance form vs a process-tensor witness; (3) THE key question — does the process-tensor
> witness resolve Flag #1 (quantum memory EXPRESSED on the PASSIVE record) or does it require
> active interventions; (4) which tool certifies the 2-qubit COLLECTIVE shared-bath channel;
> (5) remaining confirmed-literature-gaps. **Verdict: Flag 0 CONFIRMED (revival ≠ quantum);
> Flag 1 STAYS OPEN — every literature-grade quantum-memory witness is an ACTIVE-interventional
> object.**

## Metadata [ours]

- **Type:** synthesis + predict-before-measure pre-registration (theory-fix closure of Flag 0).
- **Settled result being grounded (NOT re-litigated):** entanglement/negativity REVIVAL
  (backflow) of a reduced-channel Choi = RHP non-CP-divisibility = NON-MARKOVIANITY, and it is
  FORGEABLE by classical non-Markovian noise. In-house Control 0b: classical RTN dephasing
  FIRES a bare negativity-revival witness while the genuine Bäcker `C♯(t1) < C(t2)` stays SILENT.
- **The error being corrected:** our earlier "Control 3b" dropped the '#' (used a bare revival
  `C(t2) > C(t1)`), so it witnessed MEMORY/non-Markovianity, NOT quantum memory.

## Executive summary [ours]

The four sources converge, from four independent directions, on ONE statement: **a bare
revival / backflow witnesses temporal MEMORY (the kernel / non-Markovianity / CP-indivisibility),
not the QUANTUMNESS of that memory.** Nakagawa 2601.18822 shows this constructively (same
backflow functional, same α≃1/2 boundary on the quantum and classical sides). Bäcker 2510.19522
states it operationally (a bare revival is "a sufficient criterion for CP-indivisibility" ONLY;
the quantum upgrade needs the `#`/assistance bound). Giarmatzi 1811.03722 and Taranto 2307.11905
give the multi-time formal home (classical memory = SEPARABLE process matrix / a strict class CM
BELOW the SEP/QM boundary; classical non-Markovian forgeries live strictly below quantum memory).
**Flag 0 is closed: revival ≠ quantum memory, and our RTN-forges-revival result (Control 0b) is a
published-grade fact.**

The correct tool to BUILD is the **E♯<E entanglement-of-assistance form** — extend our
Control-3 `C♯<C` to a negativity-of-assistance / bound-criterion for d>2 — because it is the
cheapest sufficient witness with a closed form (d=2) or analytic Fei/Chen bounds (d>2), directly
matched to our shared-mode σ− collective target. The process-tensor witness (Giarmatzi/Taranto)
is STRICTLY more sensitive but **requires ACTIVE local CP-map interventions with output
feed-forward** — so it does NOT resolve Flag #1 in the passive direction. **Flag #1 stays OPEN:
no source in this set certifies quantum memory on a PASSIVE syndrome record; every witness reads
an active-interventional object (Choi tomography or an instrument-varied process tensor).** This
is a STOP-consistent finding — consistent with our standing worry that quantum memory may be
twirled out of the passive record.

## Key equations/criteria [paper] (verbatim, per source)

### (A) Nakagawa 2601.18822 — backflow is kernel-driven, quantum/classical-symmetric

- Backflow functional (verbatim): `N_I ≡ ∫₀^∞ Θ(İ(t)) İ(t) dt` = total upward variation of an
  information-like observable `I(t)`. Quantum instantiation `b_qe^(α)(t) = (1/4)[E_α(−λ^α t^α)]² sin²(ωt)`;
  classical instantiation `H(t) = −Σ_{i=1}^3 p_i(t) ln p_i(t)`.
- Memory kernel = Caputo fractional derivative order `α∈(0,1]`, Mittag–Leffler solution `E_α`;
  `α=1` ⇒ Markovian exponential, `0<α<1` ⇒ long-tailed power-law memory.
- Phase boundary at `α ≃ 1/2` in the `(α, ω/λ)` plane, appearing IDENTICALLY on quantum and
  classical sides.
- Verbatim conclusion: the boundary "originates from the kernel's mathematical structure rather
  than from quantumness per se" and "the α≃1/2 boundary is a kernel-driven feature that appears
  on both the quantum and classical sides once the same memory kernel is imposed."

### (B) Bäcker 2510.19522 — the applied `C♯<C` assistance witness (the '#' RETAINED)

- Classical memory, Eq. (1): `E_t1[ρ]=Σ_i K_i ρ K_i†`, `E_t2[ρ]=Σ_i Φ_i[K_i ρ K_i†]`.
- Choi embedding, Eq. (2): `ρ^{SA}_t = (E_t ⊗ 1_A)|Φ+⟩⟨Φ+|`.
- **THE WITNESS, Eq. (3):** `C♯(ρ^{SA}_t1) < C(ρ^{SA}_t2) ⇒ memory must be QUANTUM`, where
  `C` = concurrence of FORMATION (Wootters), `C♯` = concurrence of ASSISTANCE. d=2 closed form.
- **Bare revival is WEAKER (Sec. III.B.1, verbatim):** an increase in entanglement with the
  ancilla "is also a sufficient criterion for the dynamics D=(E_t1,E_t2) to be CP-indivisible" —
  i.e. non-Markovianity ONLY, not quantum memory.
- d>2 BOUND criterion, Eq. (10): `C♯>(t1) < C<(t2)`; upper bound on assistance, Eq. (11):
  `C♯> = sqrt(2(1 − tr(tr_A(ρ_SA)^2)))` (purity-based, Li–Fei); lower bound on formation, Eq. (12):
  `C< = m̃·max(||(ρ_SA)^{T_S}||−1, ||(ρ_SA)^{T_A}||−1)`, `m̃=sqrt(2/(m(m−1)))` (partial-transpose norm, Chen–Albeverio–Fei).
- Measured: single-qubit `C♯(t1)=0.51 < 0.62=C(t2)` (Eq. 7); toy 2-qubit `C♯>(t1)=0.72 < 0.89=C<(t2)` (Eq. 14).

### (C) Giarmatzi–Costa 1811.03722 — process-tensor witness = temporal entanglement of W

- Quantum memory ⟺ process matrix `W` is ENTANGLED across the temporal cut `A_I | A_O B_I`.
- Classical memory = SEPARABLE: `W_Cl = Σ_j ρ_j^{A_I} ⊗ T_j^{A_O B_I} ⊗ …` (each term PSD;
  environment = classical feedback register measuring the system each step).
- Markovian = no-sum tensor product `W_M = ρ^{A_I} ⊗ T^{A_O B_I} ⊗ …`.
- Witness = Hermitian `Z` with `⟨Z⟩ = Tr(Z W_Cl) ≥ 0` for ALL classical-memory processes;
  `Tr(Z W) < 0` certifies quantum memory. Found via SDP (PPT → DPS symmetric-extension hierarchy).
- Operational (decisive, verbatim): "an experimenter can intervene on the system, e.g. by measuring
  or transforming it. Each operation can be represented by a completely positive map"; "measuring
  the witness only requires performing the CP maps … and does not require full process tomography."

### (D) Taranto 2307.11905 — strict multi-time hierarchy, classical memory = EBC feed-forward

- **Hierarchy (Thm 1, N≥3, STRICT):** `M ⊊ CDC ⊊ CM ⊊ SEP ⊊ QM`.
- Classical Memory (CM), Def. 3 / Eq. (12): built from ENTANGLEMENT-BREAKING CHANNELS (EBCs) on
  the environment between times; EBC = measure-and-prepare `E_o^i = Σ_x σ_o^(x) ⊗ M_i^(x)`.
- Feed-forward (verbatim): "The classical label corresponding to any observed outcome x1 can be
  stored and fed forward to condition the overall choice of any future EBC."
- Two-time collapse (verbatim): "For two-time processes, CM and CDC coincide"; separations genuine
  only for `N≥3`.

## Relevance to project [ours] — the five adjudications

### (1) Flag-0 verdict: revival ≠ quantum memory — CONFIRMED (strongest citations)

**GROUNDED.** A bare Choi/negativity/concurrence revival witnesses NON-MARKOVIANITY /
CP-indivisibility / temporal MEMORY, never the QUANTUMNESS of that memory. Strongest citations,
in order of decisiveness for us:

1. **`[paper 2601.18822]` (constructive forgery certificate)** — Nakagawa puts quantum
   entanglement revival and classical entropy overshoot on the SAME backflow functional `N_I`
   with the SAME Mittag–Leffler/Caputo-α kernel and finds the SAME `α≃1/2` phase boundary on BOTH
   sides: the boundary "originates from the kernel's mathematical structure rather than from
   quantumness per se." This is the published constructive proof that a bare revival cannot
   distinguish quantum from classical memory — it makes our Control-0b (RTN forges negativity
   revival) a published-grade fact.
2. **`[paper 2510.19522]` (operational statement in the applied witness)** — Bäcker labels the
   bare revival "a sufficient criterion for … CP-indivisible" ONLY, and requires `C♯(t1)<C(t2)`
   (assistance = classical-memory bound) for the quantum upgrade.
3. **`[paper 2307.11905]` (formal home)** — the classes `M ⊊ CDC ⊊ CM` are all non-Markovian yet
   all strictly BELOW the SEP/QM boundary: a process can have strong classical memory and fire a
   bare revival while being provably classical.

`[ours]` Our dropped-'#' "Control 3b" is exactly the "CP-indivisible but still classical-memory"
mistake these three sources separate. Verdict FIRM.

### (2) The correct tool to BUILD: E♯<E assistance form (BUILD) vs process-tensor witness (defer)

**BUILD the E♯<E assistance form.** Extend our certified Control-3 `C♯<C` (concurrence of
assistance below concurrence of formation) to the negativity-of-assistance / Fei–Chen
bound-criterion for `d>2`, matched to the shared-mode σ− collective 2-qubit target.

Tradeoffs, tagged:
- `[paper 2510.19522]` **Assistance form — cheapest sufficient witness.** d=2 has CLOSED FORM
  (Wootters + concurrence-of-assistance), no convex-roof optimization; d>2 has ANALYTIC bounds
  `C♯> = sqrt(2(1−tr(tr_A(ρ_SA)²)))` (purity, Eq. 11) and `C<` (partial-transpose norm, Eq. 12).
  It reads a two-time DYNAMICAL MAP (Choi), not a full process tensor — "comparably low
  experimental effort." This is directly implementable in our carrier from the Choi of the
  teacher channel at two times.
- `[paper 1811.03722 / 2307.11905]` **Process-tensor witness — strictly more sensitive but heavier
  and interventional.** Giarmatzi's `Tr(Z W)<0` (SDP over separability) and Taranto's CM-class
  membership carry MORE information (Bäcker verbatim: the process tensor "is more sensitive in
  detecting quantum memory [60]"), and give the genuine multi-time classical-vs-quantum boundary.
  BUT they require an SDP-derived witness AND active instrument-varying data, and — decisively for
  us — they DO NOT operate on a passive record (see (3)).
- `[ours]` **Recommendation:** BUILD the assistance form as the primary Flag-0 tool (extends
  existing Control-3 machinery, closed-form/bounded, matches the σ− target). Keep the process-tensor
  witness as the STRICTLY-STRONGER reference oracle for a future active-interventional milestone,
  NOT as the passive-record tool. Caveat `[ours]`: for `N=2` the CM/CDC classical-memory distinction
  COLLAPSES (Taranto: "For two-time processes, CM and CDC coincide") — the genuine multi-time
  classical/quantum separation is a `N≥3` phenomenon, so a two-time map witness is intrinsically
  weaker than a `N≥3` process tensor; the assistance form is the right sufficient witness, not the
  complete characterization.

### (3) THE key question — does the process-tensor witness resolve Flag #1 (passive record)?

**NO. It requires ACTIVE interventions, so it does NOT close Flag #1.** This is the decisive
finding of the synthesis.

- `[paper 1811.03722]` Giarmatzi's process matrix `W` is defined operationally through local CP
  maps the experimenter APPLIES at each "measurement station," with the OUTPUT wire `A_O` of one
  time fed forward into the next station's input `B_I`. Verbatim: "an experimenter can intervene on
  the system, e.g. by measuring or transforming it. Each operation can be represented by a
  completely positive map." Measuring the witness "only requires performing the CP maps … and does
  not require full process tomography" — it SAVES tomography but STILL requires performing the
  interventions.
- `[paper 2307.11905]` Taranto's classical-memory class is defined by ENTANGLEMENT-BREAKING
  CHANNELS inserted BETWEEN the experimenter's operations whose classical outcomes are FED FORWARD
  to condition future dynamics — an active instrument-varying object; the whole CM-vs-QM distinction
  is a property probed by VARYING instruments.
- `[paper 2510.19522]` Bäcker independently confirms the direction: its own witness is computed
  from ACTIVE state tomography of a Bell-prepared ancilla-coupled Choi state, and it explicitly
  DEFERS process-tensor tomography as future work.

`[ours]` **Consequence for Flag #1:** a PASSIVE syndrome record is a fixed non-interventional
readout with no output wire being re-prepared/propagated. From it you can build only a classical
multi-time OUTCOME distribution, NOT the process matrix `W` and NOT the instrument-varied CM/QM
object. Therefore **neither the assistance witness (active Choi tomography) nor the process-tensor
witness (active CP-map interventions) certifies quantum memory on our passive record.** Flag #1
stays OPEN, and it points at the active-vs-passive gap — consistent with our standing worry that
quantum memory is twirled out of the passive record. This is a STOP-consistent conclusion: **do NOT
claim quantum memory is expressed on the passive syndrome record on the strength of any witness in
this set.** Closing Flag #1 in the passive direction is a SEPARATE, currently UNGROUNDED question —
it requires either (a) a theorem that the passive multi-time record inherits the CM/QM separation
(none of the four sources supplies this; Taranto's `N=2` collapse is evidence AGAINST it being free),
or (b) demonstrating that our passive syndrome record actually contains the requisite temporal
entanglement, which we have no literature-grade tool for.

### (4) Which tool certifies the 2-qubit COLLECTIVE shared-bath channel?

**The Bäcker d>2 bound criterion `C♯>(t1) < C<(t2)` (Eqs. 10–12) is the usable analytic tool — but
NO source provides a working hardware/certified demonstration on a genuinely collective channel.**

- `[paper 2510.19522]` The Fei/Chen analytic bounds (Eqs. 11–12) are dimension-general and apply to
  the 3-qubit Choi of a 2-qubit dynamics — so the assistance witness IS available in principle for
  the collective shared-bath channel. BUT the paper's physically-motivated COLLECTIVE 2-qubit
  dynamics (Eq. 8, a shared single-qubit environment coupling both system qubits — structurally near
  our shared-mode σ− target) FAILED to witness quantum memory (>500 gates, decoherence dominates,
  `C♯` ≈ const, "close to random unitary dynamics … almost no quantum memory"). The toy that DID
  witness (Eq. 13) is DELIBERATELY FACTORIZED — a product `U_{S1E1}⊗U_{S2E2}` with NO system–system
  interaction — chosen to remove the collective coupling and save gates.
- `[paper 1811.03722]` Giarmatzi's process-tensor framework is dimension-general (finite d, multi-qubit,
  any N) — scaling is not the obstacle; the active-instrument data requirement is. So it CAN in
  principle certify a collective channel, but only as an active-interventional object.
- `[ours]` **Recommendation:** use the Bäcker `C♯> < C<` bound criterion on the exact Choi of our
  collective σ− teacher channel (we compute the channel exactly in-carrier, so we avoid the hardware
  gate-count wall that killed Bäcker's Eq. 8). This is the only literature-grade tool that both
  handles d>2 AND is applicable to a collective channel — but it certifies the ACTIVE channel object,
  not the passive record (per (3)). No source supplies a certified collective-channel witness to
  merely cite; we must compute it ourselves against the exact Choi, with the assistance bounds as the
  witness.

### (5) Remaining confirmed-literature-gaps

Tagged `[ours]`, each confirmed by the absence of a covering statement across all four full-text notes:

- **G-passive (Flag #1 — the big one):** NO source certifies quantum memory on a PASSIVE
  non-interventional multi-time record. Every witness is active (Choi tomography or instrument-varied
  process tensor). No theorem that the passive syndrome record inherits the CM/QM separation exists in
  this set; Taranto's `N=2` CM=CDC collapse is evidence that the separation is NOT free at few times.
  **This is the standing active-vs-passive gap and it is UNCLOSED.**
- **G-collective-cert:** NO certified/hardware demonstration of quantum memory on a genuinely
  COLLECTIVE shared-bath 2-qubit channel. The only tool is the Bäcker `C♯>< C<` bound applied to an
  exact Choi (our own computation); Bäcker's own collective attempt (Eq. 8) FAILED and their success
  (Eq. 13) is factorized.
- **G-Nlt3:** at `N=2` the classical-memory hierarchy COLLAPSES (Taranto: CM=CDC). A two-time-map
  witness (assistance form) is intrinsically weaker than a genuine `N≥3` multi-time separation. If we
  want the full classical-vs-quantum-memory boundary (not just a sufficient witness), we need `N≥3`
  process-tensor data — which is active and heavier.
- **G-negativity-of-assistance-d>2:** the assistance form for d>2 in this set is given only via the
  purity/partial-transpose BOUNDS (Eqs. 11–12), which are SUFFICIENT-but-loose. A tight
  negativity-of-assistance for our d>2 collective Choi is not supplied by any source — we would extend
  Control-3's `C♯<C` to a bound-criterion, accepting the looseness. (Non-firing under a loose bound is
  inconclusive, not a null result.)

## Predict-before-measure prereg [ours] (corrected path)

Epistemic classes per `docs/METRICS.md` (a) exact, (b) prediction band, (c) heuristic gate:

- **(a) exact:** Control 0b invariant — classical RTN dephasing FIRES a bare negativity-revival
  witness AND leaves the Bäcker `C♯(t1)<C(t2)` assistance witness SILENT. (Zero-tolerance:
  `C♯(t1) ≥ C(t2)` must hold for the RTN forgery to floating precision.) This is the corrected-tool
  positive-vs-negative discriminability check.
- **(b) prediction band (registered bet):** on the genuine shared-mode σ− collective teacher channel,
  the Bäcker `C♯>(t1) < C<(t2)` bound criterion (Eqs. 10–12) FIRES on the exact 3-qubit Choi in the
  underdamped/near-resonant regime (matched to the concurrence-revival corner already seen in-house at
  γ=0.15), and does NOT fire in the motional-narrowing / overdamped regime. A MISS is a finding, not
  later citable as fact.
- **(c) heuristic gate:** Flag #1 STOP — do not assert quantum memory on the passive record. The
  active `C♯<C` / process-tensor witnesses are the ONLY grounded tools and they read active objects;
  any passive-record quantum-memory claim is BLOCKED until a passive-inheritance theorem or a
  passive-record temporal-entanglement demonstration exists (neither in this set).

## Decisive verbatim quotes [paper]

- `[2601.18822]` "...indicating that the boundary originates from the kernel's mathematical structure
  rather than from quantumness per se." / "the α≃1/2 boundary is a kernel-driven feature that appears
  on both the quantum and classical sides once the same memory kernel is imposed."
- `[2510.19522]` "C♯(ρ^{SA}_t1) < C(ρ^{SA}_t2), where C is the concurrence of formation and C♯ is the
  concurrence of assistance, the memory has to be quantum and the dynamics cannot be realized with
  classical memory." / (bare revival) "is also a sufficient criterion for the dynamics D=(E_t1,E_t2)
  to be CP-indivisible." / (deferred) "the process tensor … is more sensitive in detecting quantum
  memory [60]."
- `[1811.03722]` "an experimenter can intervene on the system, e.g. by measuring or transforming it.
  Each operation can be represented by a completely positive map." / "measuring the witness only
  requires performing the CP maps … and does not require full process tomography." / "a process matrix
  with classical memory is proportional to a separable state."
- `[2307.11905]` "The classical label corresponding to any observed outcome x1 can be stored and fed
  forward to condition the overall choice of any future EBC." / (Thm 1, N≥3) "M ⊊ CDC ⊊ CM ⊊ SEP ⊊ QM."
  / "For two-time processes, CM and CDC coincide."

## Tags

- `[ours]` Flag 0 CONFIRMED: revival = non-Markovianity/CP-indivisibility; the '#'/assistance
  (`C♯<C`) or process-tensor temporal-entanglement form = quantum memory. Strongest citation for the
  forgery = Nakagawa 2601.18822 (kernel-driven, quantum/classical-symmetric backflow).
- `[ours]` BUILD the E♯<E assistance form (extend Control-3 `C♯<C`; closed-form d=2, Fei/Chen bounds
  d>2); process-tensor witness is stronger but active + heavier — keep as reference oracle.
- `[ours]` Flag 1 STAYS OPEN: process-tensor witness (Giarmatzi/Taranto) requires ACTIVE
  interventions (CP maps / EBC feed-forward), does NOT certify quantum memory on the PASSIVE record.
- `[ours]` Collective 2-qubit: Bäcker `C♯>< C<` bound on the exact Choi is the usable tool; no source
  supplies a certified collective demonstration (Bäcker's own Eq. 8 failed; Eq. 13 is factorized).
- `[ours]` Confirmed gaps: G-passive (Flag #1 unclosed), G-collective-cert, G-Nlt3 (CM=CDC collapse at
  N=2), G-negativity-of-assistance-d>2 (only loose bounds).
