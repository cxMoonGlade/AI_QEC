# Axis-1 incoherent-collapse set — M4 (T1), M5 (T2 dephasing), M24 (thermal) — pre-registration

Date: 2026-06-30. Status: **theory-first pre-registration** (Axis-1 rebuild group 1).
Governs: `docs/twin_validation/axis1_rebuild_plan.md`. Discipline: `FAITHFULNESS_PROTOCOL.md` +
`METRICS.md` epistemic ladder. **All physical-reference equations below were text-verified against
the extraction in `outputs/papers/`; no equation number is asserted that was not read from the
source. (N&C section numbers are conventionally-attributed; the Kraus matrices are verified via
Arsenijević 1606.01145 + the Error-Correction Zoo.) Cert `cert_m4_m5_m24_collapse.py`: ALL PASS
(2026-06-30, RTX 5090); two independent reviewers SOUND/MINOR, fixes folded in below.**

## 0. Scope and the ≥2-DIRECT bar

Three same-substep GKSL **collapse** mechanisms on the computational subspace:
- **M4 = amplitude_damping (T1)** — downward jump `c = √γ₁ · σ⁻`, `σ⁻=|0><1|`, `γ₁ = 1/T1`.
- **M5 = idle_dephasing (T2 pure dephasing)** — dephasing jump; carrier form `c = √(2γ_φ)·n`,
  `n=diag(0,1)`, equivalent to `√(γ_φ/2)·Z` (see §3 convention ledger), `γ_φ = 1/T_φ`.
- **M24 = thermal_excitation (T1↑)** — upward jump `c = √γ↑ · σ⁺`, `σ⁺=|1><0|`. M4+M24 in one
  Lindbladian = generalized amplitude damping (GAD) at finite temperature.

These are textbook channels; the ≥2-DIRECT bar is met by (i) a physical superconducting-qubit
reference that exhibits/measures the mechanism AND (ii) a second independent physical measurement
or first-principles derivation. The channel *form* additionally has a math reference (N&C / a
microscopic-derivation paper). Math-form references are logged but do not by themselves satisfy the
*physical* bar.

## 1. Grounding — ≥2 DIRECT physical references per mechanism (text-verified)

### M4 — amplitude damping / T1
- **DIRECT-1 (first-principles + measurement): Krantz, Kjaergaard, Yan, Orlando, Gustavsson,
  Oliver, "A Quantum Engineer's Guide to Superconducting Qubits," Appl. Phys. Rev. 6, 021318
  (2019); arXiv:1904.06560; DOI 10.1063/1.5089550.** [`outputs/papers/1904.06560.txt`, 67 pp.]
  Longitudinal relaxation `Γ1 ≡ 1/T1 = Γ1↓ + Γ1↑`; excited-state population decays as `exp(−Γ1 t) =
  exp(−t/T1)`; microscopic origin `Γ1 ∝ |<0|∂Ĥ/∂λ|1>|² S_λ(ω_q)` (transverse noise PSD at ω_q);
  measured-T1 protocol (Xπ → delay → exponential fit). "pure dephasing" (×16) / "transverse
  relaxation" (×6) present in text; the AD physics is the §III.B Bloch–Redfield treatment.
- **DIRECT-2 (measurement): Place et al., "New material platform for superconducting transmon
  qubits with coherence times exceeding 0.3 milliseconds," Nat. Commun. 12, 1779 (2021);
  arXiv:2003.00024; DOI 10.1038/s41467-021-22030-5.** [`outputs/papers/2003.00024.txt`, 37 pp.]
  Verbatim: "coherence times exceeding 0.3 milliseconds"; "the longest published T1 is 114 µs";
  best T1 = 0.36 ms (tantalum transmon). T1 measured by π-pulse → exponential decay of `Pₑ(t) =
  e^{−t/T1}`. Anchors the physical T1 magnitude bracket (tens–hundreds µs).
- **MATH-FORM: N&C §8.3.5 (amplitude damping)** `K0=[[1,0],[0,√(1−γ)]], K1=[[0,√γ],[0,0]]`,
  corroborated independently by Arsenijević et al. arXiv:1606.01145 (microscopic AD Kraus
  derivation) and the Error-Correction-Zoo amplitude-damping matrices. (N&C section number is
  conventionally-attributed; the matrices are verified.)

### M5 — idle dephasing / T2 pure dephasing
- **DIRECT-1: Krantz et al. arXiv:1904.06560 (Fig. 4c/d).** [text-verified verbatim]
  "(c) Pure dephasing in the transverse plane arises from [longitudinal Z noise that fluctuates the
  qubit frequency]"; "(d) … results in a **loss of coherence at a rate Γ2 = Γ1/2 + Γφ**, due to a
  combination of energy relaxation and pure dephasing." → the standard `1/T2 = 1/(2T1) + 1/T_φ`,
  and pure dephasing = longitudinal (Z/number-operator) coupling — exactly the carrier's
  `D[√(2γ_φ)·n]`.
- **DIRECT-2 (measurement): Place et al. arXiv:2003.00024.** [text-verified] "T2,Echo … 0.20 ± 0.03
  ms"; "time-averaged **T2,CPMG of 0.38 ± 0.11 ms**." Physical T2 in real transmons. CAVEAT
  (reviewer): echo/CPMG are *dynamically-decoupled* T2 — they refocus low-frequency dephasing and
  thus OVER-estimate the bare free-induction `T_φ` that the time-local `D[√(2γ_φ)n]` represents; a
  conservative bracket, and `T_φ` magnitude is class (b)/swept anyway.
- **MATH-FORM: N&C §8.3.6 (phase damping)** `K0=diag(1,√(1−λ)), K1=diag(0,√λ)`, **independently
  verified** via Arsenijević, Jeknić-Dugić, Dugić, "Microscopic derivation of the one-qubit Kraus
  operators for amplitude and phase damping," arXiv:1606.01145 [`outputs/papers/1606.01145.txt`]:
  microscopic Lindblad `dρ/dt = r(σ_z ρ σ_z − ρ)` (their Eq. 48) → Kraus `{√(1−p/2)I, √(p/2)σ_z}`,
  `p=1−e^{−2rt}`, "completeness relation for the Kraus matric[es]" satisfied (text-confirmed);
  coherence decays `e^{−2rt}` (≡ `e^{−γ_φ t}` per density-matrix off-diagonal with `r=γ_φ/2`).
- **PROVENANCE NOTE (honest):** Ithier et al. PRB 72, 134519 (2005) / cond-mat/0508588 is the
  canonical quantronium dephasing measurement and is a *real* paper, but **its arXiv PDF text layer
  did not extract** (both PyMuPDF and poppler yield no body text — only figure labels). Its
  equation numbers are therefore **NOT cited** here (anti-fabrication: no equation asserted that was
  not read). Krantz + Place carry the physical ≥2-DIRECT bar without it.

### M24 — thermal excitation / T1↑ (finite-T, GAD)
- **DIRECT-1 (measurement): Jin et al., "Thermal and Residual Excited-State Population in a 3D
  Transmon Qubit," PRL 114, 240501 (2015); arXiv:1412.2772; DOI 10.1103/PhysRevLett.114.240501.**
  [text-verified verbatim] "excited-state population … consistent with a Maxwell-Boltzmann
  distribution … over 35–150 mK. **Below 35 mK, the excited-state population saturates at
  approximately 0.1%** … effective temperature **Teff = 35 mK**." Grounds residual `P(|1>)` / `T_eff`
  → steady-state `p_∞`.
- **DIRECT-2 (measurement + mechanism): Wenner et al., "Excitation of superconducting qubits from
  hot non-equilibrium quasiparticles," PRL 110, 150502 (2013); arXiv:1209.1674; DOI
  10.1103/PhysRevLett.110.150502.** [title text-verified — corrects a wrong title in the research
  brief] hot non-equilibrium quasiparticles drive excited-state population in SC qubits — physical
  origin of the upward `σ⁺` rate.
- **SUPPORTING (in-repo, per-round rate): McEwen et al., Nat. Commun. 12, 1761 (2021);
  arXiv:2102.06131** — upward heating ~0.1%/round (leakage-inclusive; order-of-magnitude anchor,
  not the |0>→|1> floor).
- **MATH-FORM: generalized amplitude damping** (N&C §8.3.5, finite-T): 4-Kraus
  `E0=√q diag(1,√(1−γ)), E1=√q[[0,√γ],[0,0]], E2=√(1−q)diag(√(1−γ),1), E3=√(1−q)[[0,0],[√γ,0]]`.

## 2. Carrier implementation (already present — to be re-verified, not rewritten)
- M4: `forward/channels.py::amplitude_damping_kraus` (K0/K1 above); MCWF/Lindblad primitive
  `T1` → `√(γ₁)·σ⁻` (`mechanisms/axis1_primitives.py`, `σ⁻` = `sm_a`).
- M5: `T2` primitive → `√(2γ_φ)·n` (`axis1_primitives.py`); `forward/channels.py::
  phase_damping_canonical_kraus` (N&C diag form); `thermal_relaxation_kraus` enforces
  `1/T_φ = 1/T2 − 1/(2T1)`, `T2 ≤ 2T1`, `ρ01 → e^{−t/T2}ρ01`.
- M24: `T1_UP` primitive → `√γ↑·σ⁺`; `forward/channels.py::thermal_excitation_kraus`. Modeled as a
  SEPARATE σ⁺ collapse alongside M4 (M4+M24 ⇒ GAD steady state automatically).
- **Two lowering surfaces (reviewer):** `axis1_primitives.lower_two_qubit_axis1_primitives` (the cert
  path) and the MCWF `_collapse_operator` (`axis1_mcwf_mps_execution.py`) build the SAME operators
  (`√(2γ_φ)` applied at term construction). This prereg certifies the **GKSL collapse path**, NOT
  `mechanism_channel(spec)` — whose M5 is a Pauli-Z *stochastic* channel (a different, coarser PTM
  object), not the `√(2γ_φ)n` dephasing collapse.

## 3. Epistemic classes + convention ledger
- **(a) exact:** the collapse-operator forms and Kraus operators (operator identities); `ΣK†K=I`;
  the closed-form decays `P₁(t)=e^{−t/T1}` (M4), `ρ01(t)=e^{−γ_φ t}` (M5), steady-state
  `p_∞=γ↑/(γ↑+γ↓)` (M24); detailed balance `γ↑/γ↓=e^{−ħω/kT}`.
- **(b) prediction band:** the T1/T2/T_eff *magnitudes* (Krantz/Place/Jin brackets) — swept.
- **(c) gate / convention:** the rate↔probability bridge (`γ₁` rate vs `γ=1−e^{−t/T1}` prob);
  the `n`-vs-`Z` dephasing-collapse choice; the substep-vs-integrated siting.
- **Convention ledger (state explicitly to avoid a false-discrepancy):** carrier `c=√(2γ_φ)·n` with
  `n=(I−Z)/2` gives off-diagonal decay rate `γ_φ`; the identity piece of `n` drops out of `D[c]`;
  equivalent Z-form is `√(γ_φ/2)·Z`. The `√2` is the `n→Z` conversion, **not** different physics.
  Density-matrix off-diagonal decays `e^{−γ_φ t}` (hand-derived from `D[√(2γ_φ)n]`, rate `γ_φ`).
  Mapped to the canonical phase-damping `λ`-form: `√(1−λ)=e^{−γ_φ t}` ⇒ **`λ = 1 − e^{−2γ_φ t}`**
  (NOT `1−e^{−γ_φ t}` — a self-caught earlier slip; the per-amplitude `√(1−λ)` IS the off-diagonal
  factor for phase damping, so `λ=1−e^{−2γ_φ t}` gives off-diagonal `e^{−γ_φ t}`).

## 4. Constraint ledger (physical theorems + a FALSIFYING test each)
Independent ground truth = (i) hand-typed closed-form algebra (NumPy) + (ii) the UN-renormalized
operator-sum Kraus from `forward/channels.py` + (iii) the hand-typed collapse OPERATOR.
`assemble_substep_channel` is generic GKSL machinery (mechanism-agnostic: `expm(L·dt)`→Choi→Kraus)
— legitimately the carrier path under test for DYNAMICS, **never** the independent oracle.
**CPTP/TP is checked on the RAW un-renormalized Kraus** (assemble Choi-completes to CPTP, so a TP
check on ITS output is renorm-masked/vacuous — reviewer catch). Each invariant has a broken-input
falsifier that MUST trip (all verified — cert green 2026-06-30).

| # | invariant (class) | falsifier (must FAIL on a corrupted channel) |
|---|---|---|
| L1 | M4 **RAW**-Kraus `ΣK†K=I` (channels.py AD, un-renormalized) ≤1e-12 (a) | scale K1→1.3K1 ⇒ ‖ΣK†K−I‖=2.7e-2 caught (verified) |
| L2 | M4 `P₁(t)=e^{−t/T1}` over t/T1∈{0.1..3} (a) | wrong sign `e^{+t/T1}` ⇒ caught |
| L3 | M4 coherence `ρ01→e^{−t/2T1}ρ01` (AD-only) (a) | a dephasing leak (extra Z) ⇒ ρ01 factor ≠ e^{−t/2T1} caught |
| L4 | **(LOAD-BEARING triangulation)** carrier Lindblad-rate `P₁` == channels.py integrated AD-Kraus `P₁` == `e^{−t/T1}` (a) | mismatched γ₁↔1/T1 ⇒ caught |
| L5 | M5 **RAW** phase-damping `ΣK†K=I` (channels.py, λ=1−e^{−2γ_φt}) (a) | λ>1 ⇒ caught |
| L6 | M5 off-diagonal `e^{−γ_φ t}`, populations UNCHANGED (a) | a population leak (σ⁻ contamination) ⇒ ρ00,ρ11 move ⇒ caught |
| L7 | M5 `n`↔`Z` equivalence: `D[√(2γ_φ)n]` and `D[√(γ_φ/2)Z]` give identical ρ01 decay (a) | use `√(2γ_φ)Z` (wrong norm) ⇒ 4× rate ⇒ caught |
| L8 | M24 `p_∞=γ↑/(γ↑+γ↓)` exact (a) | swap γ↑↔γ↓ ⇒ p_∞ wrong ⇒ caught |
| L9 | M24 GAD `ΣEᵢ†Eᵢ=I` for all q,γ (a) | drop E3 (upward) ⇒ not TP ⇒ caught |
| L10 | M24 detailed balance `γ↑/γ↓=e^{−ħω/kT}` ↔ target T_eff (b-check) | T_eff→0 must give γ↑→0 (pure M4) ⇒ caught |
| L11 | anti-circular: cert hand-types reference operators; structural guard asserts `_collapse_operator`/`_coherent_family_generator`/`_embed_coherent_generator` NOT imported as reference (verified) | a reference built FROM `_collapse_operator` would false-pass a corrupted `_collapse_operator` ⇒ forbidden |

## 5. Bounded simplifications (declared + bounded)
- **S1 Markovian, time-local (c):** single-substep GKSL; cross-cycle T1/T2 drift is Axis-2.
  Bound: exact within a substep; drift `O(ΔT1/T1)` out of scope here.
- **S2 substep rate vs integrated Kraus (c):** carrier uses rate `γ₁`; integrated map uses
  `γ=1−e^{−t/T1}`; agree to `O((γ₁dt)²)`. Cert states which siting is under test.
- **S3 M4 = T=0 limit (a-bounded):** pure σ⁻ sets `γ↑=0`; finite-T correction IS M24 (declared,
  not omitted). Bound: exact once M24 is included.
- **S4 magnitudes swept (b):** T1∈[tens,hundreds µs] (Place), P(|1>)∈[0.1%,~5%] (Jin + planar
  regime); not frozen.

## 6. Verification plan (serialized GPU; one cert script)
`outputs/twin_validation/cert_m4_m5_m24_collapse.py` (scripted-execution: asserts + printed
evidence + flushed + `__main__` guard):
1. Build carrier channels via `lower_two_qubit_axis1_primitives`→`assemble_substep_channel` (generic
   GKSL, the path under test); build hand-typed closed-form references + RAW un-renormalized Kraus
   (channels.py) independently. Hand-type the reference collapse operators (do NOT import
   `_collapse_operator`).
2. Assert L1–L11 (operator identities + raw-Kraus CPTP + closed-form decays at ≤1e-12; falsifiers
   trip). DONE → cert green (ALL PASS).
3. Report process/entanglement infidelity vs identity (field-standard, `METRICS.md`) as a
   secondary scalar.
4. GPU run is serial; multi-agent review of this prereg + the carrier code is read-only.

## 7. Status
- [x] Theory-first grounding (≥2-DIRECT physical per mechanism, text-verified; Ithier dropped for
  unreadable extraction, Place substituted; McEwen 2102.06131 fetched).
- [x] Reading notes committed: Krantz 1904.06560, Place 2003.00024, Jin 1412.2772, Wenner 1209.1674,
  Arsenijević 1606.01145 (all close-read from extracted text; verbatim equations).
- [x] Multi-agent doc review: physics reviewer SOUND (recomputed all closed forms); faithfulness
  reviewer MINOR (anti-circular wording, raw-vs-assembled TP, L4 promotion) — all folded in.
- [x] Cert `outputs/twin_validation/cert_m4_m5_m24_collapse.py` — serialized GPU (RTX 5090), **ALL
  PASS** (operator identities exact; raw-Kraus CPTP genuine, falsifier trips at 2.7e-2; L4
  triangulation; M24 p_∞=0.2308 exact; 4 falsifiers trip).
- [x] Self-caught fix: §3 canonical-λ mapping corrected to `λ=1−e^{−2γ_φt}`.
- [ ] Final metric + rigor audit folded into group-10 integration.

**Verdict: M4 / M5 / M24 — DONE. Physically correct (≥2 DIRECT each, text-verified), CPTP-exact,
independent-GT certified (anti-circular), reviewed. Carrier code unchanged (already faithful).**
