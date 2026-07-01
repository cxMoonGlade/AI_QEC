# M8 coherent_rzz_overrotation — pre-registration (theory-first, LITERATURE-GROUNDED)

Date: 2026-06-30. Status: **theory-first pre-registration** (Axis-1 rebuild group 3; the residual/
always-on ZZ — previously implemented in the carrier but never written up). Governs:
`docs/twin_validation/axis1_rebuild_plan.md`. Discipline: `FAITHFULNESS_PROTOCOL.md` + `METRICS.md`.
**All cited equations text-verified against `outputs/papers/` extractions + committed reading notes.**

## 0. The mechanism (anchored; REUSE existing carrier code)

**M8 = coherent_rzz_overrotation** — the **always-on / residual ZZ** coherent coupling, the most
ubiquitous parasitic 2-qubit Hamiltonian in fixed-frequency and tunable-coupler transmons. Carrier
form (`mechanisms/axis1_primitives.py` "ZZ" primitive):

```
H_M8 = ζ · (n ⊗ n) = ζ · |11><11|,   n = diag(0,1)     (cross-Kerr / conditional-phase)
U_M8 = exp(−i H_M8 t) = diag(1, 1, 1, e^{−iζt})         (φ_ζ = ζ·t)
```

This is the **conditional-phase (cross-Kerr) form**: only `|11>` acquires phase. It matches
Pettersson-Fors Eq. 6 `U_ζ = diag(1,1,1,e^{−iφ_ζ})` exactly. (`zeta_rad_per_ns` is the ZZ rate.)

**Convention note (declare to avoid a false discrepancy).** The catalog/`error_mechanisms.md`
nickname "RZZ(ε)" suggests the Pauli form `exp(−iε Z⊗Z/2)`. The carrier implements the
**physically-real cross-Kerr** `ζ·|11><11|`, which relates to the Pauli form by
`|11><11| = n⊗n = (I⊗I − I⊗Z − Z⊗I + Z⊗Z)/4` — i.e. cross-Kerr = `Z⊗Z` Pauli term **plus local
single-qubit Z rotations + a global phase**. The *physical* residual-ZZ IS the conditional phase
(Pettersson-Fors/Mundada measure exactly `ζ·|11><11|`-type shifts), so the carrier form is the
correct device object; the local-Z difference is an `M6/M7`-type single-qubit frame, not part of M8.

## 1. Grounding — ≥2 DIRECT physical references (text-verified)

This is the **best-grounded** 2q coherent mechanism (residual ZZ is genuinely always-on in real
hardware), and unlike pure XX/YY it is exhibited in **isolation** device-physically:

- **DIRECT-1: Pettersson Fors et al., "Comprehensive explanation of ZZ coupling," arXiv:2408.15402
  (Chalmers, 2024).** [`outputs/papers/2408.15402.txt`; note `pettersson_fors_zz_coupling_
  comprehensive_2408.15402.md`] ZZ = cross-Kerr `ζ = E'₁₁−E'₁₀−E'₀₁+E'₀₀ ∝ σz⊗σz` (Eq. 3);
  conditional-phase unitary `U_ζ = diag(1,1,1,e^{−iφ_ζ})` (Eq. 6) — **the carrier's exact form**;
  CZ-regime `ζ̄ = 2π×5 MHz`, coherence-limited edge `2π×100 kHz`.
- **DIRECT-2: Mundada, Zhang, Hazard, Houck, "Suppression of Qubit Crosstalk in a Tunable Coupling
  Superconducting Circuit," PRApplied 12, 054023 (2019); arXiv:1810.04182.** [note in-repo]
  **measured residual ZZ `ζ/2π = 2.26 MHz`** (off-null), suppressed via destructive coupler-path
  interference. A direct device measurement of the always-on longitudinal ZZ.
- **DIRECT-3 (induced-ZZ derivation): Geller-Martinis arXiv:1405.1915** Eq. 82/85 — the gmon coupler
  *induces* a diagonal `J σz⊗σz` (`J ≈ g²/η`, ~kHz, Fig. 10) alongside the transverse XX. Device
  first-principles derivation of the induced ZZ.
- (Supporting only, NOT counted: Kubo 2402.05361 cites residual ZZ −60..−80 kHz from its ref [20],
  not its own Google measurement.)

Bar: **≥2 DIRECT-physical MET decisively** (Pettersson-Fors + Mundada, both device-direct; Geller a
third).

## 2. Epistemic classes
- **(a) exact:** `H_M8 = ζ·|11><11|` operator identity; `U = diag(1,1,1,e^{−iζt})`; closed form
  `1−F_e = (3/4)·sin²(ζt/2)` (entanglement fidelity, `F_e=|Tr U/d|²`, d=4); leading `3(ζt)²/16`.
- **(b) prediction band:** the ζ magnitude — `ζ/2π ∈ [~0.1, ~5] MHz` (Mundada 2.26 MHz measured;
  Pettersson-Fors CZ-edge 5 MHz / coherence-edge 100 kHz) — swept, not frozen.
- **(c) gate / convention:** the cross-Kerr-vs-Pauli-Z⊗Z convention (local-Z frame); siting.

## 3. Closed form (independent ground truth, derived by hand)
For `U = diag(1,1,1,e^{−iφ})`, `φ=ζt`: `Tr U = 3 + e^{−iφ}`, `|Tr U|² = 10 + 6cosφ`, so
`F_e = (10+6cosφ)/16` and **`1−F_e = (6−6cosφ)/16 = (3/4)sin²(φ/2)`**, leading `3φ²/16`. (Distinct
from the traceless single-Pauli-pair `sin²(ε/4)` — because `n⊗n` is NOT traceless: `Tr(n⊗n)=1`.)

## 4. Constraint ledger (physical theorems + FALSIFYING test each)
Independent GT = hand-typed `ζ·kron(n,n)` + closed form (NumPy); `assemble_substep_channel` is the
generic GKSL path under test; the cert hand-types the reference (does NOT import `_collapse_operator`/
family builders — structural guard).

| # | invariant (class) | falsifier (must trip) |
|---|---|---|
| L1 | operator identity `H_carrier("ZZ") == ζ·\|11><11\|` ≤1e-12 (a) | use `ζ·kron(n,I)` (1-site) ⇒ ‖·‖>1e-3 caught |
| L2 | `U = diag(1,1,1,e^{−iζt})` exact (a) | wrong sign `e^{+iζt}` ⇒ caught |
| L3 | `1−F_e = (3/4)sin²(ζt/2)` (a) | use the traceless `sin²(ε/4)` formula ⇒ mismatch caught |
| L4 | conditional-phase: `\|00>,\|01>,\|10>` UNCHANGED, only `\|11>` phase (a) | a `Z⊗I` contamination ⇒ `\|10>` also phases ⇒ caught |
| L5 | unitary ⇒ CPTP `‖ΣK†K−I‖≤1e-12` (a) | — (structural; unitary) |
| L6 | anti-circular: reference hand-typed; `_collapse_operator` not imported (structural) | ref built from carrier op false-passes corruption ⇒ forbidden |

## 5. Bounded simplifications
- **S1 cross-Kerr (a-bounded):** carrier = `ζ·|11><11|` (Pettersson-Fors Eq. 6 exact); the Pauli-Z⊗Z
  difference is local-Z + global phase (M6/M7 frame), declared, bounded (exact up to that frame).
- **S2 static ζ (b):** ζ constant across the substep; cross-cycle ζ-drift is Axis-2. Bound `O(Δζ/ζ)`.
- **S3 magnitude swept (b):** ζ/2π∈[0.1,5] MHz (Mundada/Pettersson-Fors), not frozen.

## 6. Verification plan (serialized GPU)
`outputs/twin_validation/cert_m8_zz.py` (scripted: asserts + printed evidence + flushed + `__main__`):
lower the "ZZ" primitive → `assemble_substep_channel`; assert L1–L6 vs hand-typed GT; falsifiers trip.

## 7. Status
- [x] Theory-first grounding (≥2 DIRECT-physical, text-verified; reading notes already in repo).
- [x] Cert `outputs/twin_validation/cert_m8_zz.py` — serialized GPU (RTX 5090), **ALL PASS**:
  L1 operator identity exact (0.00e+00); L3 `1−F_e=(3/4)sin²(ζt/2)=0.007475`; L4 conditional phase
  (only `|11>`-coherences phase by +0.2; `|00>-|10>` unchanged); CPTP; F2 distinguishes cross-Kerr
  from traceless-pair (0.007475 vs 0.002498); 3 falsifiers trip.
- [ ] Multi-agent review (folded into group-3 review).
- Carrier code: already implements the correct cross-Kerr form — re-verified, NOT rewritten.
