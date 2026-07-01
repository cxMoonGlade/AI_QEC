# Architecture synthesis — scalable COUPLED (correlated + non-Markovian) QEC-noise teacher

**Date 2026-06-30.** Synthesis of 10 full-text 精读 reading notes (committed under
`docs/papers/reading_notes/`) from the cross-field deep research, mapped onto our requirement:
keep the coupling (correlated dissipation + non-Markovian memory) + full-2D + multi-round +
independent exact oracle. Load-bearing papers still need my personal 精读-verify before any code
(per theory-first); this note is the design, not a build authorization. Epistemic tags: (a) exact,
(b) grounded-literature/prediction, (c) heuristic/gate.

## The 10-paper landscape (by role)

**Independent ORACLES for the coupled non-Markovian regime (few-qubit, exact, method-distinct from our MCWF):**
- **ACE / PT-MPO `[2405.19319]` — STRONGEST.** A single PT-MPO with a **collective** coupling operator
  `Â=Σᵢ Oᵢ` gives a genuine **shared bath across qubits** — correlated dephasing (`Â=ΣZᵢ`) AND collective
  dissipation (`D[Σσᵢ⁻]`, §IV.G), non-Markovian-native, ships polaron/TEMPO/analytic cross-checks.
  Independent of our engine (path-integral C++). Ceiling ~30 composite levels (≈few qubits). **Oracle, not
  carrier.** Caveat: collective-*dissipation* demo is Markovian → fully-non-Markovian collective χ needs a pilot.
- **Chain-mapping Block-Lanczos `[2407.10140]`.** Shared bath → block-tridiagonal ladder, correlation carried
  EXACTLY in off-diagonal blocks; both σz/σ⁻ admissible; a-priori light-cone/excitation bounds; independent
  (satisfies anti-toy Rule I). Ceiling **≤6 emitters/6 excitations**, **bosonic bath only** (discrete-TLS 1/f
  doesn't fit natively), no QEC-circuit wrapper.
- **T-TEDOPA `[2606.30569]`.** Cross-correlated bath via off-diagonal `J_lm(ω)` → long-range chain (HEOM
  cannot). 2–4 qubits, Gaussian bath. **Key: the discriminating observable is coherence decay `|ρ_nm(t)|`,
  not populations** — matches our own "correlation lives in coherence, twirled out of syndromes" finding.
- **Collisional-TN `[2202.04697]`** — single-qubit within-bath oracle; gives a falsifiable ledger constraint
  (Eq. 8: memory kernel ∝ connected 2-point bath correlator + stroboscopic rate renormalization).
- **Time-invariant PT `[2603.06840]`** — single-qubit oracle; points to its ref [30] for coupled-PT.

**2D-geometry CARRIER (the scale fix):**
- **tePEPO `[2512.01781]`.** A 2D iPEPO mixed-state method, area-law bond `D`, that **structurally relieves
  the 1D `2^(2d)` bond wall** which made our d3-as-1D-MPS slow. Ships toric-code FSA rules. **BUT
  Markovian-only** (Lindblad generator; no influence functional/memory kernel). Its own stated route to
  non-Markovian: **embed explicit bath/ancilla (pseudomode) sites, evolve the enlarged system Markovianly.**

**TEMPORAL-MEMORY closure:**
- **GLE kernel-learning `[2402.11705]`.** The **only a-priori-bounded** route (Thm 4.2: kernel error linearly
  bounded by correlation-function error, computable constant). Bounded for **Lorentzian/TLS** memory; **voids
  for a hard 1/f power-law** (branch cut) — but **1/f *is* a TLS/Lorentzian ensemble, so a finite Lorentzian
  pseudomode bank is both physically faithful AND in the bounded regime.** Complex modes preserve the
  **coherence-revival** (our non-Markovian wedge). Single-qubit temporal only (spatial/matrix = future work).
- **Mori-Zwanzig `[1611.03311]`** — the derived-closure FRAMEWORK; classical (no CPTP), so not a direct
  recipe, but its finite-memory→auxiliary-ODE bank is the **classical twin of a pseudomode unraveling**.
- **NZ ⇔ influence-functional `[2312.13233]`** — memory-kernel and process-tensor are **exactly
  inter-convertible for a single effective system + Gaussian bath** (Dyck-path map), so those two ingredients
  are ONE and any truncation has an exact kernel reading (good for bounded-simplification discipline). BUT
  the equivalence **BREAKS for spatially-coupled qubits (Class 3) — explicitly future work.**

**FACTORIZES (wrong direction — excluded):**
- **PT-MPO+TEBD chains `[2201.05529]`** — factorizes the bath per-site *by explicit assumption* (verbatim:
  shared/inter-site baths "outside the scope"); 1D-only; using it as our oracle would be **circular** (shares
  our exact blind spot). A cautionary counter-model, not a tool.

## The architecture that emerges (a COMPOSITION — no single paper has it)

1. **Carrier = 2D iPEPO (tePEPO family)** — right geometry, area-law, relieves the 1D `2^(2d)` wall. Markovian. `[2512.01781]`
2. **Memory = pseudomodes** — represent the shared 1/f/TLS source as a **finite bank of Lorentzian
   pseudomodes** (= the physical TLS ensemble = the *bounded* regime of `[2402.11705]`). A **shared** pseudomode
   coupled to multiple qubits carries the CORRELATED, non-Markovian dephasing + collective dissipation.
   Embedding → the enlarged (qubits + pseudomodes) system is **Markovian** → runs on the iPEPO carrier AND our
   existing MCWF engine. This is the "carry the source explicitly" line. `[1611.03311, 2512.01781]`
3. **Oracle = ACE (primary) + chain-mapping + T-TEDOPA** — few-qubit **independent exact GT** for the coupled
   non-Markovian regime; validate the pseudomode-truncated carrier at ≤~6 qubits. This is the anti-circular
   certification **the field concedes it lacks** (QMCtwin). `[2405.19319, 2407.10140, 2606.30569]`
4. **Observable = coherence-sensitive** — the signal lives in `|ρ_nm|` / coherence-revival, not raw syndrome
   populations `[2606.30569]` — consistent with our earlier finding (the cross-cycle-syndrome-correlation
   observable was a Kam-benign strawman; coherence is twirled out of the syndrome stream).

## The genuine open frontier = our contribution
The composition **pseudomodes-on-2D-iPEPO, oracle-validated** is in **no single paper** — the memory-kernel↔PT
equivalence *breaks* exactly at coupled qubits `[2312.13233]`; tePEPO is Markovian `[2512.01781]`; the coupled
oracles stop at ≤6 qubits `[2405.19319, 2407.10140]`. Composing them, with the few-qubit oracle as the
anti-circular certificate, is the novel, defensible move — and the oracle itself (an independent exact GT for
correlated non-Markovian QEC noise) is a standalone methodological contribution.

## Honest risks (must be oracle-validated, not trusted)
- **(c)** Pseudomode sites inflate the iPEPO bond dim exactly where its simple-update truncation is already
  shaky (`ξ≳2`) `[2512.01781]` — the composition's central feasibility risk.
- **(b)** The a-priori memory bound is **single-qubit temporal only**; the multi-site *coupled* bound is open
  `[2402.11705, 2312.13233]` — so multi-qubit faithfulness rests on the empirical oracle cross-check, not a theorem.
- **(a)** "Diagonalize the bath-correlation matrix → independent baths" is NOT free — a declared, error-bounded
  (rule III) simplification whose error surfaces in coherence `[2606.30569]`.
- Chain-mapping/T-TEDOPA oracles are **bosonic/Gaussian** — a discrete-TLS 1/f source needs a Lorentzian/pseudomode
  bridge to use them; ACE (non-Gaussian) is the more general oracle.

## RECENT-LITERATURE UPDATE (2025–2026) — the core method is PUBLISHED (de-risks the plan)

A second 精读 pass on the *recent* frontier (user push: "找近期的文献") changed the picture: the memory
carrier + the multi-qubit shared-bath assembler I framed as "our novel step" are **already published**.

- **Coupled-Lindblad-Pseudomode `[2506.10308, PRL 136 090403, 2026]` — THE memory carrier + shared-bath
  assembler.** The enlarged (qubits ⊗ N pseudomodes) evolution is an **exact CPTP GKSL channel, no memory
  kernel** (Eq. 2) → runs as-is on our MCWF / 2D-iPEPO carrier (pseudomodes = truncated-Fock bosonic sites).
  **SM §S2 does the multi-qubit shared bath**: coupling generalizes to a matrix `g∈C^{N×n}`, `Ĥ_SA=Σⱼ Ŝⱼ Âⱼ`,
  **matrix-valued BCF** → one pseudomode set couples to multiple qubits = **cross-qubit correlated noise**.
  **polylog(T/ε)** mode count + a **convex SDP** construction (no non-convex fit). Conditional on SDP
  feasibility (Eq. 7) + `J(ω)` analyticity — re-confirm on our QEC BCFs. Gaussian bath (1/f as Lorentzian-sum
  = in scope; a strongly-coupled non-Gaussian single TLS is out → bracket).
- **Markovian-Embeddings unification `[2602.21430, JCP 2026]`.** HEOM ⇔ Lindblad-pseudomode ⇔ thermofield-MPS
  are ONE Gaussian unraveling of the bath self-energy; our 1/f/TLS sits in the **exact Lorentzian regime**
  (class-(a) exact up to the Lorentzian fit + Fock truncation); the CPTP **Lindblad-pseudomode form (Eq. 33)**
  is the one to feed our carrier; closed-form `C(t)`/`J(ω)` GT (Rule-I anchor). Single-site.
- **Correlated-noise embedding `[2509.19685, 2025]`.** The pole→pseudomode→exact-Lindblad recipe (single-site
  primitive) + closed-form GT (Eq. 40–45); flags the load-bearing **RWA-breaking `n_max` cost** — pseudomode
  truncation relies on excitation preservation, which QEC X/Y/CZ gates BREAK → cost unquantified (our pilot).
- **PT-aware decoder `[2412.13739, 2024]`.** Gives the **ML process-tensor-aware decoder** (Choi/link-product
  TN, LER-by-contraction) — HIGH reuse. Confirms correlated noise **raises the *optimal* LER**, BUT runs no
  mismatched-Markov baseline → the **PT-vs-Markov decode-relevant ΔLER is OURS to measure**; and its HS metric
  is **coherence-blind** — reinforcing that our wedge needs coherence-sensitive scoring. d3, single-round,
  per-qubit private bath (not shared-latent).
- **Exact correlated threshold `[2510.24181, 2025]`.** Closed-form edge rule `p̄₂=2(1−p₂)p₂` → random-bond
  Ising; a theorem-grade **Rule-I anchor for the *spatial-NN-correlated stochastic-Z BASELINE*** (certify
  seam). Confirms spatial correlation is decode-relevant (~0.5–0.6% matching headroom vs exact 3%) — but it is
  **static/Markovian/Pauli = the owned/removable baseline, NOT the non-Markovian wedge.**

### Updated architecture (concrete + de-risked)
1. **Memory + shared-bath: coupled-Lindblad-pseudomode `[2506.10308]`** — matrix coupling `g∈C^{N×n}` for the
   cross-qubit shared bath; fit our real-device 1/f/TLS as a Lorentzian sum; exact CPTP GKSL on the enlarged
   space; polylog modes (verify on our BCFs).
2. **2D carrier: tePEPO iPEPO `[2512.01781]`** — the enlarged (qubits + pseudomodes) system is Markovian →
   runs on the area-law 2D carrier (relieves the 1D `2^(2d)` wall).
3. **Oracle: ACE `[2405.19319]` (+ chain-mapping / T-TEDOPA / closed-form `C(t)`/`J(ω)`)** — few-qubit
   independent exact GT for the coupled non-Markovian regime; the anti-circular certificate the field lacks.
4. **Decoder + observable: PT-aware ML decoder `[2412.13739]` + a COHERENCE-sensitive metric** — the
   PT-vs-Markov ΔLER (decode-relevant) is the headline WE produce; scored coherence-sensitively.
5. **Baseline anchor: exact threshold `[2510.24181]`** — closed-form check for the spatial-Markovian owned part.

### Our NARROWED contribution (the core method is now cited, not invented)
- **The QEC application of coupled-Lindblad-pseudomode:** the **RWA-breaking `n_max` cost** (QEC gates break
  excitation preservation — the concrete open feasibility risk), multi-round space-time records, the
  **PT-vs-Markov decode-relevant ΔLER** (coherence-sensitive), full-2D via the iPEPO composition, real-device
  1/f/TLS BCF grounding.
- **The independent-oracle certification methodology** (ACE + closed-form GT) at few qubits — the anti-circular
  GT QMCtwin concedes the field lacks.
- **The non-Markovian (CP-divisibility-breaking, coherence-revival) wedge**, cleanly separated from the two
  owned baselines: spatial-Markovian `[2510.24181]` and coherent-coupling (QMCtwin).

### Key open feasibility questions a small-scale pilot must answer (before any scale build)
(a) does the polylog pseudomode scaling hold for our QEC BCFs (SDP feasibility)? (b) does the coherence-revival
wedge survive N=3–4 pseudomode truncation? (c) the **RWA-breaking `n_max` cost** under QEC gates? (d) does
pseudomode+iPEPO stay tractable where the iPEPO simple-update is already shaky (`ξ≳2`)?

## Next (theory-first)
Personal 精读-verify ACE `[2405.19319]`, chain-mapping `[2407.10140]`, and the GLE bound `[2402.11705]` against
the extracted text; then a pre-registration for **(1) the few-qubit independent oracle** (ACE/chain-mapping on a
2–4-qubit shared-bath patch — the standalone contribution + the certificate) BEFORE the carrier, and only then
**(2) the pseudomode-on-2D-carrier** design with the oracle as its acceptance gate.
